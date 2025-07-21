import os
import json
import requests
import pandas as pd
import subprocess
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from datetime import datetime, timedelta
from urllib.parse import urljoin
from openai import OpenAI

from functions_eventos import DB_API_URL, api_request, mensaje_chat_gpt

def generar_destinatario(numero):
    if numero == "+56977566595":
        return "Cristobal"
    elif numero == "120363027104819888@g.us":
        return "Collahuasi"
    elif numero == "+56971083001":
        return "Ricardo"
    elif numero == "+56982280571":
        return "Hector Veliz"
    elif numero == "+56976426949":
        return "Daniel"
    elif numero == "+56939496396":
        return "equipo del turno de automatizacion de la mina"
    else:
        return "Collahuasi"  

def saludo_inicial_hora(hora):
     if 8 <= hora < 12:
         return "Buenos dias"
     elif 12 <= hora <= 20:
         return "Buenas tardes"
     else:
         return "Buenas noches"


def obtener_alertas(url_alertas, horas_atras = 8, minutos_atras = 0, fecha_exacta = None):
    """Consulta la API para obtener alertas urgentes."""
    if fecha_exacta:
        fecha = fecha_exacta
    else:
        now = datetime.now() - timedelta(hours=horas_atras, minutes=minutos_atras)
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")  # Convertir a formato ISO 8601
        fecha = now_str

    url_alertas_full = url_alertas + f"?fecha={fecha}"
    print(url_alertas_full)
    #url_alertas = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"]) + f"?fecha=2025-03-01T00:00:00"
    #print(url_alertas)
    alertas = api_request(url_alertas_full, dataframe=False)

    if not alertas:
        print("No hay alertas urgentes.")
        sys.exit(0)

    # Clasificar alertas
    señal_deficientes = [i for i in alertas if "señal deficiente" in i.lower()]
    interferencias = [i for i in alertas if "interferencia" in i.lower()]
    
    return señal_deficientes, interferencias

def enviar_whatsapp_mudslide(id, mensaje, timeout=10):
    """Envía un mensaje a un usuario o grupo de WhatsApp usando Mudslide."""
    env = os.environ.copy()
    env["NODE_OPTIONS"] = "--experimental-global-webcrypto"

    # 🔹 Usar `--` antes del mensaje para evitar problemas con `-`
    #comando = f'NODE_OPTIONS=--experimental-global-webcrypto mudslide send {id} -- "{mensaje}"'
    #comando = f'NODE_OPTIONS=--experimental-global-webcrypto mudslide send {id} -- "Prueba de mensaje"'
    comando = f'npx mudslide@latest send {id} "{mensaje}"'
    print(f"Comando a ejecutar: {comando}")

    try:
        resultado = subprocess.run(comando, shell=True, env=env, capture_output=True, text=True, check=True, timeout=timeout)
        print(f"✅ Mensaje enviado correctamente a {id}")

    except subprocess.TimeoutExpired:
        raise TimeoutError(f"❌ Timeout: No se recibió respuesta de WhatsApp en {timeout} segundos para {id}.")
    except subprocess.CalledProcessError as error:
        print(f"❌ Error al enviar mensaje a {id}: {error.stderr}")


def enviar_correo_html(remitente, clave, destinatarios, asunto, html):
    """Envía un correo electrónico con contenido HTML."""

    mensaje = MIMEMultipart("alternative")
    mensaje["From"] = remitente
    mensaje["To"] = ", ".join(destinatarios)
    mensaje["Subject"] = asunto

    # Adjuntar HTML al mensaje
    mensaje.attach(MIMEText(html, "html"))

    # Enviar
    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(remitente, clave)
        servidor.sendmail(remitente, destinatarios, mensaje.as_string())
        servidor.quit()
        print("✅ Correo HTML enviado con éxito.")
    except Exception as e:
        print("❌ Error al enviar el correo:", e)