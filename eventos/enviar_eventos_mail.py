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
from functions_eventos import DB_API_URL, api_request, mensaje_chat_gpt
from functions_enviar_eventos import obtener_alertas, generar_destinatario, enviar_correo_html, saludo_inicial_hora

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

api_key='API_KEY'
client = OpenAI(api_key=api_key)

url_alertas = urljoin(DB_API_URL, config["api"]["eventos"]["get"])
url_alertas_urgentes = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"])

def generar_mensaje_correo(tabla_alertas, tipo_alerta, empresa):
    """Genera un mensaje para correo basado en las alertas y el tipo (señal deficiente o interferencias)."""
    print(f"Generando mensaje de alerta para {tipo_alerta}.")
    if tipo_alerta == "señal deficiente":
        valor = "latencia"
    else:
        valor = "interferencia"
        
    mensaje_prompt = f"""
    Eres un asistente que generará un informe breve para enviar por email sobre {tipo_alerta}. Estas alertas las detecta un producto de software de HCG-GROUP llamado "Smartlink" el cual es un software para monitoreo de equipos de telecomunicaciones en faenas mineras. En cuestion haras el resumen del turno, de las ultimas 8 horas.
    
    Recuerda ser cordial y presentarte brevemente (SIN SALUDAR PORQUE EL SALUDO YA SE HACE ANTES DE QUE TE LLEGUE ESTA INFO A TI), en modo de introduccion. En la introduccion menciona que el mensaje proviene de Smartlink de HCG-Group para ayudar a {empresa} (solo menciona esto pero en tus palabras no agreges nada mas que sea redundante), y tambien menciona el para que es este mensaje. Se breve. Comienza con algo asi de "Este es un mensaje de "
    
    El mensaje debe ser breve, claro y conciso, con un tono profesional y amigable.

    Aqui esta la tabla en html que debe in incluida para este tipo de alerta:

    {tabla_alertas}

    (A veces la tabla puede ser que no se haya generado, en ese caso simplemente pon el mismo mensaje que coloca mi funcion para crear la tabla)
    
    
    Responde con un mensaje listo para enviar por correo electrónico.
    """
    return mensaje_chat_gpt(client=client, mensaje=mensaje_prompt)

def crear_tabla(alertas, tipo_alerta):
  """Crea una tabla HTML con columnas adaptadas al tipo de alerta."""

  tipo_alerta_titulo = f"Alertas de {tipo_alerta.capitalize()}"

  if not alertas:
    return f"<h2>{tipo_alerta_titulo}</h2><p>No hay alertas para mostrar.</p>"

  # Columnas base
  columnas = ["fecha", "estado", "ip", "tag", "marca", "tipo", "recurrencia"]

  # Agregar columnas específicas según tipo
  if tipo_alerta.lower() == "señal deficiente":
    columnas += ["latencia mas alta"]
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

    señal_deficientes_urgentes, interferencias_urgentes = obtener_alertas(
        url_alertas_urgentes=DB_API_URL,
        horas_atras=args.hours_ago,
        minutos_atras=args.minutes_ago,
    )
    hora_actual = datetime.now().hour
    saludo_inicial = saludo_inicial_hora(hora_actual)

    crear_tabla_señales = crear_tabla(señal_deficientes_urgentes, "señal deficiente")
    crear_tabla_interferencias = crear_tabla(interferencias_urgentes, "interferencias")

    guardar_como_html(crear_tabla_señales)
    guardar_como_html(crear_tabla_interferencias)


    mensaje_señales = generar_mensaje_correo(crear_tabla_señales, "señal deficiente", empresa)
    mensaje_interferencias = generar_mensaje_correo(crear_tabla_interferencias, "interferencias", empresa)


    enviar_correo_html(
        remitente=remitente,
        clave=clave,
        destinatarios=destinatarios,
        asunto=f"Alertas y alarmas de {empresa}",
        mensaje=mensaje_señales,
    )
    