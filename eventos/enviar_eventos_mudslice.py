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
from functions_enviar_eventos import obtener_alertas, generar_destinatario, enviar_whatsapp_mudslide, saludo_inicial_hora

load_dotenv("/usr/smartlink/eventos/.env")

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

api_key=os.getenv("OPEN_API_KEY")
print("api_key", api_key)
client = OpenAI(api_key=api_key)


def generar_mensaje_whatsapp(alertas, tipo_alerta, empresa):
    """Genera un mensaje para WhatsApp basado en las alertas y el tipo (señal deficiente o interferencias)."""
    print(f"alertas recibidas:\n{alertas}")
    print(f"Generando mensaje de alerta para {tipo_alerta}. Cantidad de alertas: {len(alertas)}")
    if not alertas:
        return None  # No generamos mensaje si no hay alertas
    if tipo_alerta == "señal deficiente":
        valor = "latencia"
    else:
        valor = "interferecia"
        
    mensaje_prompt = f"""
    Eres un asistente que generarÃ¡ un informe breve para WhatsApp sobre {tipo_alerta}. Estas alertas las detecta un producto de software de HC-GROUP (Asi tal cual, todas las letras en mayusculas y con el guion) llamado "Smartlink" el cual es un software para monitoreo de equipos de telecomunicaciones en faenas mineras. En cuestion haras el resumen del turno, de las ultimas 8 horas.
    
    Recuerda ser cordial y presentarte brevemente (SIN SALUDAR PORQUE EL SALUDO YA SE HACE ANTES DE QUE TE LLEGUE ESTA INFO A TI), en modo de introduccion. En la introduccion menciona que el mensaje proviene de Smartlink de HC-Group para ayudar a {empresa} (solo menciona esto pero en tus palabras no agreges nada mas que sea redundante), y tambien menciona el para que es este mensaje. Se breve. Comienza con algo asi de "Este es un mensaje de "
    
    AquÃ­ estÃ¡ la lista de eventos:
    {alertas}

    Genera un mensaje de alerta que resuma los eventos mÃ¡s urgentes, destacando los de mayor prioridad.
    Usa emojis \U0001F534 para Alarmas y \U0001F7E1 para Alertas. Limita el mensaje a {num_messages} eventos.
    El formato debe ser claro y conciso, como:
    - [Fecha] \U0001F534 Equipo X - Marca - promedio del valor de {valor} - 5 veces
    - [Fecha] \U0001F7E1 Equipo Y - Marca - promedio del valor de {valor} - 2 veces

    DETALLES IMPORTANTES A CONSIDERAR:
    - El valor de recurrencia se refiere a que un equipo se ha repetido un valor importante a considerar en un rango de fechas de 15 minutos. Por ejemplo si un equipo tuvo latencia alta a las 17:00:00 y luego a las 17:15:00, entonces tendra dos valores pero uno tendra recurrencia 2. Solo muestra el valor de mayor recurrencia y el promedio de su valor, NO REPITAS EQUIPOS.
    - No obstante a veces puede ser que un equipo presento valores importantes criticos en horas distintas. En ese caso si hay que agregarlos. TEN SIEMPRE EN CUENTA EL VALOR DE RECURRENCIA!.
    - Ordenalos por fecha del mas antiguo al mas nuevo.
    
    
    Recomienda que tomen medidas o que esten atentos a estos equipos.
    Aclara que es un mensaje automatizado y que no debe responderse.
    SOLO ESCRIBE EL MENSAJE, NADA MAS.
    """

    return mensaje_chat_gpt(client=client, mensaje=mensaje_prompt)



def enviar_mensajes_whatsapp(mensaje, tipo_alerta, mudslide_id, destinatario, introduccion):
    """EnvÃ­a el mensaje por WhatsApp solo si existe."""
    if not mensaje:
        print(f"âš ï¸ No hay alertas de {tipo_alerta} para enviar.")
        return  # No ejecuta nada si el mensaje estÃ¡ vacÃ­o


    print(f"ðŸ“¤ Enviando mensaje de {tipo_alerta} a {mudslide_id}")

    try:
        # Intentar enviar con un timeout de 10 segundos
        mensaje = f"{introduccion}.\n{mensaje}"
        
        enviar_whatsapp_mudslide(mudslide_id, mensaje, timeout=60)
        print(f"âœ… Mensaje de {tipo_alerta} enviado correctamente a {mudslide_id} - {destinatario}")

    except TimeoutError:
        print(f"âš ï¸ Timeout: WhatsApp no respondiÃ³ en 10 segundos para {mudslide_id} - {destinatario}. Problemas con mudslide o conexiÃ³n.")
    except Exception as e:
        print(f"âŒ Error al enviar mensaje a {mudslide_id}: {e}")
    sleep(2)  # Esperar entre mensajes para evitar bloqueos de WhatsApp


# ðŸŸ¢ **Ejecutar el flujo**
if __name__ == "__main__":
    url_alertas_urgentes = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"])
    print(f"url_alertas_urgentes: {url_alertas_urgentes}")
    señal_deficientes, interferencias = obtener_alertas(
        url_alertas=url_alertas_urgentes,
        horas_atras=args.hours_ago,
        minutos_atras=args.minutes_ago,
    )
    
    hora_actual = datetime.now().hour
    saludo_inicial = saludo_inicial_hora(hora_actual)
    mensaje_señales = generar_mensaje_whatsapp(señal_deficientes, "señal deficiente", empresa)
    mensaje_interferencias = generar_mensaje_whatsapp(interferencias, "interferencias", empresa)
    for mudslide_id in MUDSLICE_ID_LIST:
        destinatario = generar_destinatario(mudslide_id)
        
        if destinatario == "Collahuasi":
            introduccion = f"{saludo_inicial} estimado equipo de {destinatario}"
        elif destinatario == "equipo del turno de automatizacion de la mina":
            introduccion = f"{saludo_inicial} estimado {destinatario}"
        else:
            introduccion = f"{saludo_inicial} estimado {destinatario}"

        print(f"ðŸ“¤ Enviando mensaje de señal deficiente a {mudslide_id} - {destinatario}")
        enviar_mensajes_whatsapp(mensaje_señales, "señal deficiente", mudslide_id, destinatario, introduccion)
        print(f"ðŸ“¤ Enviando mensaje de interferencias a {mudslide_id} - {destinatario}")
        enviar_mensajes_whatsapp(mensaje_interferencias, "interferencias", mudslide_id, destinatario, introduccion)

    print("Mensajes enviados correctamente.")
