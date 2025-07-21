import json
import requests
import pandas as pd
from datetime import timedelta
import subprocess
import subprocess
import shlex
import os

DB_API_URL = "http://localhost:8000/"

# Función para hacer una solicitud a la API
def api_request(url, method="GET", dataframe=False, headers=None, data=None):
    try:
        # Si 'data' es una lista, convertirla a JSON
        if isinstance(data, list):
            data = json.dumps(data)
            if headers is None:
                headers = {}
            headers["Content-Type"] = "application/json"
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, data=data)
        else:
            print(f"Unsupported method: {method}")
            return None

        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data) if dataframe else data
        else:
            print("Error al obtener datos:", response.status_code, response.text)
            return None
    except Exception as e:
        print("Request failed:", e)
        return None

# Función para redondear la fecha a los 15 minutos más cercanos
def round_to_nearest_quarter_hour(dt, return_as_string=False, iso_format_string=False):
    # Si dt es un string, lo convertimos a datetime usando pandas
    if isinstance(dt, str):
        dt = pd.to_datetime(dt)
    
    # Redondea los minutos a los 15 minutos más cercanos
    minute = dt.minute
    rounded_minute = 15 * round(minute / 15)
    
    # Si el redondeo llega a 60 minutos, ajusta la hora y los minutos
    if rounded_minute == 60:
        dt += pd.Timedelta(hours=1)
        rounded_minute = 0
    
    # Reemplaza minutos, segundos y microsegundos
    dt = dt.replace(minute=rounded_minute, second=0, microsecond=0)
    
    # Si se requiere el resultado como string, lo formateamos
    if return_as_string:
        if iso_format_string:
            return dt.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Si no, retornamos el objeto datetime
    return dt

# Función para consultar eventos anteriores usando la API
def get_eventos_previos(url_eventos_previos, tipo_evento, ip, start_date, end_date, limit=1000, offset=0, tipo_interferencia=None):
    url = f"{url_eventos_previos}/{ip}?start_date={start_date}&end_date={end_date}&limit={limit}&offset={offset}"
    data = api_request(url, dataframe=True)
    if data.empty:
        return None
    
    # Si el tipo de evento es "Interferencia", filtrar según el tipo de interferencia (snr_h o snr_v)
    if tipo_evento == "Interferencia" and tipo_interferencia:
        data["detalle"] = data["detalle"].apply(json.loads)
        data = data[data['detalle'].apply(lambda d: d.get('tipo_interferencia') == tipo_interferencia)]

    return data


# Función para calcular la recurrencia
def calcular_recurrencia(url_eventos_previos, ip, fecha_evento, tipo_evento, intervalo_recurrencia, limit=1000, offset=0, tipo_interferencia=None):
    fecha_evento = pd.to_datetime(fecha_evento)  # Convertir string ISO a datetime
    start_date = (fecha_evento - timedelta(minutes=intervalo_recurrencia, seconds=5)).isoformat()
    end_date = fecha_evento.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Consultar eventos previos en la API
    eventos_previos = get_eventos_previos(
        url_eventos_previos=url_eventos_previos,
        tipo_evento=tipo_evento,
        ip=ip,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
        tipo_interferencia=tipo_interferencia
    )
    if eventos_previos is None or len(eventos_previos) == 0:
        return 1
    # Obtener la recurrencia máxima de los eventos previos, asegurando que la columna exista
    max_recurrencia = eventos_previos["recurrencia"].max() if "recurrencia" in eventos_previos else 0
    recurrencia = max(max_recurrencia, len(eventos_previos)) + 1

    return int(recurrencia)

def mensaje_chat_gpt(client, mensaje, is_windows=False):
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": mensaje},
    ]
    )
    chat_mensaje = response.choices[0].message.content
    if is_windows:
        mensaje_sanitized = chat_mensaje.replace("\n", "\\n")
        chat_mensaje = mensaje_sanitized
    return chat_mensaje





