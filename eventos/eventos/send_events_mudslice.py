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
from functions_eventos import DB_API_URL, api_request, send_whatsapp_message_mudslide, mensaje_chat_gpt

# Leer configuraciÃ³n desde YAML
script_dir = os.path.dirname(os.path.realpath(__file__))
with open(f'{script_dir}/configEventos.yml', 'r') as file:
    config = yaml.safe_load(file)

# ConfiguraciÃ³n del parser de argumentos
parser = argparse.ArgumentParser(description='Enviar mensajes de WhatsApp.')
parser.add_argument('--num_messages', type=int, help='NÃºmero de mensajes mÃ¡ximos.', default=10)
parser.add_argument('--mudslice_id', type=str, help='ID de MudSlice para enviar mensajes.', default='id_default')
parser.add_argument('--empresa', type=str, help='Empresa de la alerta.', default='default')
parser.add_argument('--hours_ago', type=int, help='NÃºmero de horas atrÃ¡s para buscar alertas.', default=1)
parser.add_argument('--minutes_ago', type=int, help='NÃºmero de minutos atrÃ¡s para buscar alertas.', default=5)
args = parser.parse_args()

# Variables de configuraciÃ³n
num_messages = args.num_messages
empresa = args.empresa
mudslice_id = args.mudslice_id

# Obtener la lista de grupos de WhatsApp desde el YAML
MUDSLICE_ID_LIST = config['whatsapp']['mudslice'].get(mudslice_id, [])

# Inicializar cliente de OpenAI

api_key='CAMBIAR ESTA COSA A GET ENV'
client = OpenAI(api_key=api_key)


def obtener_alertas():
    """Consulta la API para obtener alertas urgentes."""
    now = datetime.now() - timedelta(hours=args.hours_ago, minutes=args.minutes_ago)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S")  # Convertir a formato ISO 8601

    url_alertas = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"]) + f"?fecha={now_str}"
    print(url_alertas)
    #url_alertas = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"]) + f"?fecha=2025-03-01T00:00:00"
    #print(url_alertas)
    alertas = api_request(url_alertas, dataframe=False)

    if not alertas:
        print("No hay alertas urgentes.")
        sys.exit(0)

    # Clasificar alertas
    senal_deficientes = [i for i in alertas if "señal deficiente" in i.lower()]
    interferencias = [i for i in alertas if "interferencia" in i.lower()]

    return senal_deficientes, interferencias

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


def generar_mensaje_whatsapp(alertas, tipo_alerta, empresa):
    """Genera un mensaje para WhatsApp basado en las alertas y el tipo (seÃ±al deficiente o interferencias)."""
    print(f"Generando mensaje de alerta para {tipo_alerta}. Cantidad de alertas: {len(alertas)}")
    if not alertas:
        return None  # No generamos mensaje si no hay alertas
    if tipo_alerta == "senal deficiente":
        valor = "latencia"
    else:
        valor = "interferecia"
        
    mensaje_prompt = f"""
    Eres un asistente que generarÃ¡ un informe breve para WhatsApp sobre {tipo_alerta}. Estas alertas las detecta un producto de software de HCG Group llamado "Smartlink" el cual es un software para monitoreo de equipos de telecomunicaciones en faenas mineras. En cuestion haras el resumen del turno, de las ultimas 8 horas.
    
    
    Recuerda ser cordial y presentarte brevemente (SIN SALUDAR PORQUE EL SALUDO YA SE HACE ANTES DE QUE TE LLEGUE ESTA INFO A TI), en modo de introduccion. En la introduccion menciona que el mensaje proviene de Smartlink de HCG-Group para ayudar a {empresa} (solo menciona esto pero en tus palabras no agreges nada mas que sea redundante), y tambien menciona el para que es este mensaje. Se breve. Comienza con algo asi de "Este es un mensaje de "
    
    AquÃ­ estÃ¡ la lista de eventos:
    {alertas}

    Genera un mensaje de alerta que resuma los eventos mÃ¡s urgentes, destacando los de mayor prioridad.
    Usa emojis ðŸ”´ para Alarmas y ðŸŸ¡ para Alertas. Limita el mensaje a {num_messages} eventos.
    El formato debe ser claro y conciso, como:
    - [Fecha] ðŸ”´ Equipo X - promedio del valor de {valor} - 5 veces
    - [Fecha] ðŸŸ¡ Equipo Y - promedio del valor de {valor} - 2 veces

    DETALLE IMPORTANTE, NO REPETIR EL EQUIPO. El equipo en cada mensaje siempre estara entre los strings "Equipo" y "presenta".
    A veces puede ser que un equipo registre dos fechas. En ese caso solo menciona a ese equipo con su fecha y su valor mas reciente, y su recurrencia mas alta registrada.
    Por ejemplo si el equipo X tiene una alerta o alarma a las 17:00:00 y luego otra a las 17:15:00, menciona solo la de las 17:15:00. Me explico?

    Recomienda que tomen medidas o que esten atentos a estos equipos.
    Aclara que es un mensaje automatizado y que no debe responderse.
    SOLO ESCRIBE EL MENSAJE, NADA MAS.
    """

    return mensaje_chat_gpt(client=client, mensaje=mensaje_prompt)

def saludo_inicial_hora(hora):
     if 8 <= hora < 12:
         return "Buenos dias"
     elif 12 <= hora <= 20:
         return "Buenas tardes"
     else:
         return "Buenas noches"


def enviar_mensajes_whatsapp(mensaje, tipo_alerta, mudslide_id, destinatario, introduccion):
    """EnvÃ­a el mensaje por WhatsApp solo si existe."""
    if not mensaje:
        print(f"âš ï¸ No hay alertas de {tipo_alerta} para enviar.")
        return  # No ejecuta nada si el mensaje estÃ¡ vacÃ­o


    print(f"ðŸ“¤ Enviando mensaje de {tipo_alerta} a {mudslide_id}")

    try:
        # Intentar enviar con un timeout de 10 segundos
        mensaje = f"{introduccion}.\n{mensaje}"
        
        send_whatsapp_message_mudslide(mudslide_id, mensaje, timeout=60)
        print(f"âœ… Mensaje de {tipo_alerta} enviado correctamente a {mudslide_id}")

    except TimeoutError:
        print(f"âš ï¸ Timeout: WhatsApp no respondiÃ³ en 10 segundos para {mudslide_id}.")
    except Exception as e:
        print(f"âŒ Error al enviar mensaje a {mudslide_id}: {e}")
    sleep(2)  # Esperar entre mensajes para evitar bloqueos de WhatsApp


# ðŸŸ¢ **Ejecutar el flujo**
if __name__ == "__main__":
    senal_deficientes, interferencias = obtener_alertas()
    hora_actual = datetime.now().hour
    saludo_inicial = saludo_inicial_hora(hora_actual)
    mensaje_senales = generar_mensaje_whatsapp(senal_deficientes, "señal deficiente", empresa)
    mensaje_interferencias = generar_mensaje_whatsapp(interferencias, "interferencias", empresa)
    for mudslide_id in MUDSLICE_ID_LIST:
        destinatario = generar_destinatario(mudslide_id)
        
        if destinatario == "Collahuasi":
            introduccion = f"{saludo_inicial} estimado equipo de {destinatario}"
        elif destinatario == "equipo del turno de automatizacion de la mina":
            introduccion = f"{saludo_inicial} estimado {destinatario}"
        else:
            introduccion = f"{saludo_inicial} estimado {destinatario}"

        print(f"ðŸ“¤ Enviando mensaje de seÃ±al deficiente a {mudslide_id} - {destinatario}")
        enviar_mensajes_whatsapp(mensaje_senales, "seÃ±al deficiente", mudslide_id, destinatario, introduccion)
        print(f"ðŸ“¤ Enviando mensaje de interferencias a {mudslide_id} - {destinatario}")
        enviar_mensajes_whatsapp(mensaje_interferencias, "interferencias", mudslide_id, destinatario, introduccion)

    print("Mensajes enviados correctamente.")
