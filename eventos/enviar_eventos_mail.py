#!usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import yaml
import pytz
import argparse
import subprocess
from time import sleep
from datetime import datetime, timedelta
from urllib.parse import urljoin
from openai import OpenAI
from dotenv import load_dotenv

from functions_eventos import DB_API_URL, api_request, mensaje_chat_gpt
from functions_enviar_eventos import obtener_alertas, generar_destinatario, enviar_correo_html, saludo_inicial_hora

load_dotenv("/usr/smartlink/eventos/.env")

# Leer configuración desde YAML
script_dir = os.path.dirname(os.path.realpath(__file__))
with open(f'{script_dir}/configEventos.yml', 'r') as file:
    config = yaml.safe_load(file)

# Configuración del parser de argumentos
parser = argparse.ArgumentParser(description='Enviar mensajes de WhatsApp.')
parser.add_argument('--num_messages', type=int, help='Número de mensajes máximos.', default=10)
parser.add_argument('--mudslice_id', type=str, help='ID de MudSlice para enviar mensajes.', default='id_default')
parser.add_argument('--empresa', type=str, help='Empresa de la alerta.', default='default')
parser.add_argument('--hours_ago', type=int, help='Número de horas atrás para buscar alertas.', default=1)
parser.add_argument('--minutes_ago', type=int, help='Número de minutos atrás para buscar alertas.', default=5)
args = parser.parse_args()


# Variables de configuración
num_messages = args.num_messages
empresa = args.empresa
mudslice_id = args.mudslice_id

# Obtener la lista de grupos de WhatsApp desde el YAML
MUDSLICE_ID_LIST = config['whatsapp']['mudslice'].get(mudslice_id, [])

# Inicializar cliente de OpenAI

api_key=os.getenv("OPEN_API_KEY")
print("api_key", api_key)
client = OpenAI(api_key=api_key)


def generar_mensaje_correo(html_tablas, empresa):
    """Genera un mensaje para correo."""
        
    mensaje_prompt = f""" 
    Eres un asistente que generará un informe breve para enviar por email sobre alertas y alarmas relacionados a latencias altas y a interferencias. Estas alertas las detecta un producto de software de HCG-GROUP (Asi tal cual, todas las letras en mayusculas y con el guion) llamado "Smartlink" el cual es un software para monitoreo de equipos de telecomunicaciones en faenas mineras. En cuestion haras el resumen del turno, de las ultimas 8 horas.
    
    Recuerda ser cordial y presentarte brevemente, y saluda al equipo de {empresa}, en modo de introduccion. En la introduccion menciona que el mensaje proviene de Smartlink de HCG-Group para ayudar a {empresa} (solo menciona esto pero en tus palabras no agreges nada mas que sea redundante), y tambien menciona el para que es este mensaje. Se breve. Comienza con algo asi de "Este es un mensaje de ".
    
    Los valores estan en estas tablas html:
    
    {html_tablas["tabla_señales"]}
    
    {html_tablas["tabla_interferencias"]}

    (A veces la tabla puede ser que no se haya generado, en ese caso simplemente pon el mismo mensaje que coloca mi funcion para crear la tabla)
    
    Las tablas deben incluirse con su titulo. Si por algun motivo hay valores repetidos en las columnas ip y fecha (fechas exactas con hora incluida), elimina un valor y solo deja el que tenga la recurrencia mas alta.
    
    Responde con un mensaje listo para enviar por correo electrónico. ESCRIBELO EN HTML ESTO ES IMPORTANTISIMO.
    PERO NO AGREGRES ```html NI NADA SIMILAR AL MENSAJE
    """
    return mensaje_chat_gpt(client=client, mensaje=mensaje_prompt)

def crear_tabla(alertas, tipo_alerta):
  """Crea una tabla HTML con columnas adaptadas al tipo de alerta."""
  print(alertas)
  tipo_alerta_titulo = f"{tipo_alerta.capitalize()}"

  if not alertas:
    return f"<h2>{tipo_alerta_titulo}</h2><p>No hay alertas para mostrar.</p>"

  # Columnas base
  columnas = ["fecha", "estado", "ip", "tag", "marca", "tipo", "recurrencia"]

  # Agregar columnas específicas según tipo
  if tipo_alerta.lower() == "señal deficiente":
    columnas += ["latencia"]
  elif "interferencia" in tipo_alerta.lower():
    columnas += ["snr_h", "snr_v"]
  elif "temperatura" in tipo_alerta.lower():
    columnas += ["temperatura"]

  # Encabezado
  html = f"<h2 style='color:#2E86C1;'>Alertas de {tipo_alerta_titulo}</h2>"
  html += "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; font-size: 13px; font-family: Arial;'>"
  html += "<thead style='background-color:#f2f2f2;'><tr>"
  for col in columnas:
    nombre_col = "nombre" if col == "tag" else col
    html += f"<th>{nombre_col.capitalize()}</th>"
  html += "</tr></thead><tbody>"

  # Filas
  for alerta in alertas:
    html += "<tr>"
    for col in columnas:
      if col == "latencia":
        valor_sin_redondear = alerta.get("latencia", "")
        if valor_sin_redondear != "":
          valor = str(round(alerta.get("latencia"),2))
      else:
        valor = alerta.get(col)
      if valor is None and isinstance(alerta.get("detalle"), dict):
        valor = alerta["detalle"].get(col)
      html += f"<td>{valor if valor is not None else ''}</td>"
    html += "</tr>"

  html += "</tbody></table><br>"
  return html

def guardar_como_html(html, nombre_archivo="alertas.html"):
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(f"""
        <html>
            <head><meta charset="utf-8"></head>
            <body>
                {html}
            </body>
        </html>
        """)
    print(f"✅ Archivo guardado como {nombre_archivo}")


if __name__ == "__main__":
    # Obtener alertas urgentes
    remitente = config["email"]["remitente"]
    clave = config["email"]["smtp_password"]
    destinatarios = config["email"]["destinatarios"]
    con_copia = config["email"]["con_copia"]
    
    url_alertas = urljoin(DB_API_URL, config["api"]["eventos"]["get"])
    url_alertas_urgentes = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"])
    print(f"url_alertas_urgentes: {url_alertas_urgentes}")
    señal_deficientes_urgentes, interferencias_urgentes = obtener_alertas(
        url_alertas=url_alertas_urgentes,
        horas_atras=args.hours_ago,
        minutos_atras=args.minutes_ago,
    )
    hora_actual = datetime.now().hour
    saludo_inicial = saludo_inicial_hora(hora_actual)

    crear_tabla_señales = crear_tabla(señal_deficientes_urgentes, "señal deficiente")
    crear_tabla_interferencias = crear_tabla(interferencias_urgentes, "interferencias")

    guardar_como_html(crear_tabla_señales, "tabla_poor_latency.html")
    guardar_como_html(crear_tabla_interferencias, "tabla_interferencias.html")

    html_tablas = {
      "tabla_señales": crear_tabla_señales,
      "tabla_interferencias": crear_tabla_interferencias
    }

    mensaje_a_enviar = generar_mensaje_correo(html_tablas, empresa)
    #mensaje_a_enviar = "Prueba de mensaje"
    

    enviar_correo_html(
        remitente=remitente,
        clave=clave,
        destinatarios=destinatarios,
        con_copia=con_copia,
        asunto=f"Alertas y alarmas de {empresa}",
        html=mensaje_a_enviar,
    )