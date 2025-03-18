import os
import yaml
import argparse
import requests
from datetime import datetime, timedelta
import pandas as pd
import json
# from globalHCG import *
from urllib.parse import urljoin
import pprint

from functions_eventos import api_request, calcular_recurrencia, round_to_nearest_quarter_hour, get_eventos_previos, DB_API_URL

# Crear un objeto PrettyPrinter
pp = pprint.PrettyPrinter(indent=4)

# Carga configuración desde YAML
script_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{script_dir}/configEventos.yml", "r") as ymlfile:
    config = yaml.safe_load(ymlfile)

start_date_default = (datetime.now() - timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S')
end_date_default = (datetime.now() + timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S')

parser = argparse.ArgumentParser(description="Script para clustering y generación de heatmaps.")
parser.add_argument('--start_date', type=str, default=start_date_default, help="Fecha de inicio de los eventos. Por defecto es la fecha actual menos 1 día.")
parser.add_argument('--end_date', type=str, default=end_date_default, help="Fecha de fin de los eventos. Por defecto es la fecha actual.")
parser.add_argument('--limit', type=int, default=1000, help="Cantidad de registros maximos a obtener.")
parser.add_argument('--offset', type=int, default=0, help="Pagina de registros a obtener.")
parser.add_argument('--intervalo_recurrencia', type=int, default=15, help="Intervalo en minutos para evaluar recurrencia. Por defecto: 15 minutos.")


args = parser.parse_args()
start_date = args.start_date
end_date = args.end_date
limit = args.limit
offset = args.offset
intervalo_recurrencia = args.intervalo_recurrencia

print(f"Fecha de inicio: {start_date}, Fecha de fin: {end_date}, Limit: {limit}, Offset: {offset}, Intervalo de recurrencia: {intervalo_recurrencia}")

# Lista de eventos
eventos = []

# Obtener datos de latencia
url_get_poor_latency = f'{urljoin(DB_API_URL, config["api"]["latencia"]["get_poor_latency"])}?start_date={start_date}&end_date={end_date}&limit={limit}&offset={offset}'
print(url_get_poor_latency)
data_latency = api_request(url_get_poor_latency)

# url eventos previos
url_eventos_previos = urljoin(DB_API_URL, config["api"]["eventos"]["get_ip"])

if data_latency is None:
    print("No se pudo obtener datos de latencia.")
    data_latency = []
else:
    print("Datos de latencia obtenidos.")
    latencias_100_200 = [d for d in data_latency if 100 <= d['latencia'] <= 200]
    latencias_mayores_200 = [d for d in data_latency if d['latencia'] > 200]

    print(f"Latencias entre 100 y 200 ms: {len(latencias_100_200)}")
    print(f"Latencias mayores a 200 ms: {len(latencias_mayores_200)}")
    
    for d in latencias_100_200:
        fecha_evento = round_to_nearest_quarter_hour(d["fecha"], return_as_string=True, iso_format_string=True)
        recurrencia = calcular_recurrencia(url_eventos_previos=url_eventos_previos, ip=d["ip"], fecha_evento=fecha_evento, tipo_evento="Señal Deficiente", intervalo_recurrencia=intervalo_recurrencia)
        urgente = recurrencia >= 3  # Marcar como urgente si recurrencia >= 3
        eventos.append({
            "ip": d["ip"],
            "fecha": fecha_evento,
            "nodo": "ap",
            "estado": "Alerta",
            "problema": "Señal deficiente",
            "detalle": {
                "latencia": d["latencia"]
            },
            "recurrencia": recurrencia,
            "urgente": urgente
        })
    for d in latencias_mayores_200:
        fecha_evento = round_to_nearest_quarter_hour(d["fecha"], return_as_string=True, iso_format_string=True)
        recurrencia = calcular_recurrencia(url_eventos_previos=url_eventos_previos, ip=d["ip"], fecha_evento=fecha_evento, tipo_evento="Señal Deficiente", intervalo_recurrencia=intervalo_recurrencia)
        urgente = recurrencia >= 3
        eventos.append({
            "ip": d["ip"],
            "fecha": fecha_evento,
            "nodo": "ap",
            "estado": "Alarma",
            "problema": "Señal deficiente",
            "recurrencia": recurrencia,
            "urgente": urgente,
            "detalle": {
                "latencia": d["latencia"]
            }
        })

# Obtener datos de Cambium
url_get_snr = f'{urljoin(DB_API_URL, config["api"]["cambium_data"]["get_snr_h"])}?start_date={start_date}&end_date={end_date}&limit={limit}&offset={offset}'
data_cambium = api_request(url_get_snr, dataframe=True)

if data_cambium is not None:
    # Extraer valores de snr_h y snr_v desde la columna snr
    data_cambium['snr'] = data_cambium['snr'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    data_cambium_snr_h = data_cambium[data_cambium['snr'].apply(lambda x: isinstance(x, dict) and 'snr_h' in x)].copy()
    data_cambium_snr_h['snr_h'] = data_cambium_snr_h['snr'].apply(lambda x: x.get('snr_h'))
    
    data_cambium_snr_v = data_cambium[data_cambium['snr'].apply(lambda x: isinstance(x, dict) and 'snr_v' in x)].copy()
    data_cambium_snr_v['snr_v'] = data_cambium_snr_v['snr'].apply(lambda x: x.get('snr_v'))
else:
    data_cambium_snr_h, data_cambium_snr_v = None, None


if data_cambium_snr_h is None:
    print("No se pudo obtener datos de Cambium (SNR H).")
else:
    print("Datos de Cambium obtenidos (SNR H)")
    print(f"Datos de Cambium (SNR H): {len(data_cambium_snr_h)}")
    
    for d in data_cambium_snr_h:
        fecha_evento = round_to_nearest_quarter_hour(d["fecha"], return_as_string=True, iso_format_string=True)
        recurrencia = calcular_recurrencia(url_eventos_previos=url_eventos_previos, 
                                           ip=d["ip"], fecha_evento=fecha_evento, 
                                           tipo_evento="Interferencia", 
                                           intervalo_recurrencia=intervalo_recurrencia,
                                           tipo_interferencia="snr_h"
                                           )
        urgente = recurrencia >= 3
        if d["snr_h"] <= 20 and d["snr_h"] > 15:
            eventos.append({
                "ip": d["ip"],
                "fecha": fecha_evento,
                "nodo": "ap",
                "estado": "Alerta",
                "problema": "Interferencia",
                "recurrencia": recurrencia,
                "urgente": urgente,
                "detalle": {
                    "snr_h": d["snr_h"],
                    "tipo_interferencia": "snr_h"
                }
            })
            
        elif d["snr_h"] <= 15:
            eventos.append({
                "ip": d["ip"],
                "fecha": fecha_evento,
                "nodo": "ap",
                "estado": "Alarma",
                "problema": "Interferencia",
                "recurrencia": recurrencia,
                "urgente": urgente,
                "detalle": {
                    "snr_h": d["snr_h"],
                    "tipo_interferencia": "snr_h"
                }
            })

if data_cambium_snr_v is None:
    print("No se pudo obtener datos de Cambium (SNR V).")
else:
    print("Datos de Cambium obtenidos (SNR V)")
    print(f"Datos de Cambium (SNR V): {len(data_cambium_snr_v)}")
    
    for d in data_cambium_snr_v:
        fecha_evento = round_to_nearest_quarter_hour(d["fecha"], return_as_string=True, iso_format_string=True)
        recurrencia = calcular_recurrencia(url_eventos_previos=url_eventos_previos, 
                                           ip=d["ip"], 
                                           fecha_evento=fecha_evento, 
                                           tipo_evento="Interferencia", 
                                           intervalo_recurrencia=intervalo_recurrencia,
                                           tipo_interferencia="snr_v"
                                           )
        urgente = recurrencia >= 3
        if d["snr_v"] <= 20 and d["snr_v"] > 15:
            eventos.append({
                "ip": d["ip"],
                "fecha": fecha_evento,
                "nodo": "ap",
                "estado": "Alerta",
                "problema": "Interferencia",
                "recurrencia": recurrencia,
                "urgente": urgente,
                "detalle": {
                    "snr_v": d["snr_v"],
                    "tipo_interferencia": "snr_v"
                }
            })
            
        elif d["snr_v"] <= 15:
            eventos.append({
                "ip": d["ip"],
                "fecha": fecha_evento,
                "nodo": "ap",
                "estado": "Alarma",
                "problema": "Interferencia",
                "recurrencia": recurrencia,
                "urgente": urgente,
                "detalle": {
                    "snr_v": d["snr_v"],
                    "tipo_interferencia": "snr_v"
                }
            })


# Insertar eventos
url_add_list = urljoin(DB_API_URL, config["api"]["eventos"]["add_list"])
print(f"Insertando {len(eventos)} eventos. URL: {url_add_list}")
pp.pprint(eventos)
if len(eventos) > 0:
    data = api_request(url_add_list, method="POST", data=eventos)
else:
    print("No hay eventos para insertar")