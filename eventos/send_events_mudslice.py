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

# Leer configuración desde YAML
script_dir = os.path.dirname(os.path.realpath(__file__))
with open(f'{script_dir}/configEventos.yml', 'r') as file:
    config = yaml.safe_load(file)

# Configuración del parser de argumentos
parser = argparse.ArgumentParser(description='Enviar mensajes de WhatsApp.')
parser.add_argument('--num_messages', type=int, help='Número de mensajes máximos.', default=10)
parser.add_argument('--mudslice_id', type=str, help='ID de MudSlice para enviar mensajes.', default='id_default')
parser.add_argument('--empresa', type=str, help='Empresa de la alerta.', default='default')
parser.add_argument('--hours_ago', type=int, help='Número de horas atrás para buscar alertas.', default=2)
parser.add_argument('--minutes_ago', type=int, help='Número de minutos atrás para buscar alertas.', default=5)
args = parser.parse_args()

# Variables de configuración
num_messages = args.num_messages
empresa = args.empresa
mudslice_id = args.mudslice_id

# Obtener la lista de grupos de WhatsApp desde el YAML
MUDSLICE_ID_LIST = config['whatsapp']['mudslice'].get(mudslice_id, [])

# Inicializar cliente de OpenAI
client = OpenAI(api_key='-')


def obtener_alertas():
    """Consulta la API para obtener alertas urgentes."""
    now = datetime.now(pytz.utc) - timedelta(hours=args.hours_ago, minutes=args.minutes_ago)
    now_str = now.isoformat()  # Convertir a formato ISO 8601

    url_alertas2 = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"]) + f"?fecha={now_str}"
    print(url_alertas2)
    url_alertas = urljoin(DB_API_URL, config["api"]["eventos"]["urgentes"]) + f"?fecha=2025-03-01T00:00:00"
    print(url_alertas)
    alertas = api_request(url_alertas, dataframe=False)

    if not alertas:
        print("No hay alertas urgentes.")
        sys.exit(0)

    # Clasificar alertas
    señal_deficientes = [i for i in alertas if "señal deficiente" in i.lower()]
    interferencias = [i for i in alertas if "interferencia" in i.lower()]

    return señal_deficientes, interferencias


def generar_mensaje_whatsapp(alertas, tipo_alerta):
    """Genera un mensaje para WhatsApp basado en las alertas y el tipo (señal deficiente o interferencias)."""
    print(f"Generando mensaje de alerta para {tipo_alerta}. Cantidad de alertas: {len(alertas)}")
    if not alertas:
        return None  # No generamos mensaje si no hay alertas
    
    mensaje_prompt = f"""
    Eres un asistente que generará un informe breve para WhatsApp sobre {tipo_alerta}.
    La empresa que recibirá este mensaje es {empresa}.
    Aquí está la lista de eventos:
    {alertas}

    Genera un mensaje de alerta que resuma los eventos más urgentes, destacando los de mayor prioridad.
    Usa emojis 🔴 para Alarmas y 🟡 para Alertas. Limita el mensaje a {num_messages} eventos.
    El formato debe ser claro y conciso, como:
    - [Fecha] 🔴 Equipo X - 5 veces
    - [Fecha] 🟡 Equipo Y - 2 veces
    Si hay más eventos, menciona que hay más incidentes sin listarlos todos.

    DETALLE IMPORTANTE, NO REPETIR EL EQUIPO. El equipo en cada mensaje siempre estara entre los strings "Equipo" y "presenta".
    A veces puede ser que un equipo registre dos fechas. En ese caso solo menciona a ese equipo con su fecha y su valor mas reciente, y su recurrencia mas alta registrada.
    Por ejemplo si el equipo X tiene una alerta o alarma a las 17:00:00 y luego otra a las 17:15:00, menciona solo la de las 17:15:00. Me explico?

    SOLO ESCRIBE EL MENSAJE, NADA MAS.
    """

    return mensaje_chat_gpt(client=client, mensaje=mensaje_prompt)



def enviar_mensajes_whatsapp(mensaje, tipo_alerta):
    """Envía el mensaje por WhatsApp solo si existe."""
    if not mensaje:
        print(f"⚠️ No hay alertas de {tipo_alerta} para enviar.")
        return  # No ejecuta nada si el mensaje está vacío

    for mudslide_id in MUDSLICE_ID_LIST:
        print(f"📤 Enviando mensaje de {tipo_alerta} a {mudslide_id}")

        try:
            # Intentar enviar con un timeout de 10 segundos
            send_whatsapp_message_mudslide(mudslide_id, mensaje, timeout=10)
            print(f"✅ Mensaje de {tipo_alerta} enviado correctamente a {mudslide_id}")

        except TimeoutError:
            print(f"⚠️ Timeout: WhatsApp no respondió en 10 segundos para {mudslide_id}.")
        except Exception as e:
            print(f"❌ Error al enviar mensaje a {mudslide_id}: {e}")
        sleep(2)  # Esperar entre mensajes para evitar bloqueos de WhatsApp


# 🟢 **Ejecutar el flujo**
if __name__ == "__main__":
    señal_deficientes, interferencias = obtener_alertas()

    mensaje_señales = generar_mensaje_whatsapp(señal_deficientes, "señal deficiente")
    mensaje_interferencias = generar_mensaje_whatsapp(interferencias, "interferencias")

    enviar_mensajes_whatsapp(mensaje_señales, "señal deficiente")
    enviar_mensajes_whatsapp(mensaje_interferencias, "interferencias")

    print("Mensajes enviados correctamente.")
