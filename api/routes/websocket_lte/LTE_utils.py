# router/websocket_lte/lte_utils.py
import random
import os
import time
import asyncio
from routes.websocket_lte.LTE_modules import get_ip_lte_ssh  # Asegúrate de tener esta función

TIPO = "LTE"
INTERVALO_TIEMPO = 5  # Segundos
MAX_TIEMPO = 5 * INTERVALO_TIEMPO
ESTADOS = {
    1: "OK",
    2: "TARDE",
    3: "DESCONECTADO"
}
script_path = os.path.abspath(__file__)
script_folder = os.path.dirname(script_path)
ssh_script_c = os.path.join(script_folder, "ssh_LTE_request")  # Ruta al archivo C

# Estado de las IPs
estado_ips = {}
estado_ultimo_tiempo_respuesta = {}

# Obtener las IPs desde la base de datos
async def obtener_ips():
    from connection import get_db_connection
    # NO SE PUEDE UTILIZAR LA API PORQUE SERIA UNA LLAMADA DENTRO DE UNA LLAMADA A LA API Y ESO CAUSA UN LOOP INFINITO
    # (No recuerdo bien el motivo teorico)
    #import requests
    # url_inventario = DB_API_URL + f"inventario/get/tipo/{TIPO}" 
    #request_inventario = requests.get(url_inventario)
    #if request_inventario.status_code == 200:
    #    inventario_data = request_inventario.json()
    #    return [record['ip'] for record in inventario_data]
    #else:
    #    print(f"Failed to fetch data. {url_inventario}\n- Status code: {request_inventario.status_code}")
    #    return []
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT ip FROM inventario WHERE tipo = %s"
    cursor.execute(query, (TIPO,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# Función para obtener la marca de tiempo y el estado de la IP
def obtener_marca_tiempo(ip, tiempo_respuesta):
    global estado_ultimo_tiempo_respuesta, estado_ips

    # Calcular la marca de tiempo
    tiempo_actual = time.time()
    estado_ultimo_tiempo_respuesta[ip] = tiempo_actual

    # Determinar el estado basado en el tiempo de respuesta
    if tiempo_respuesta < INTERVALO_TIEMPO:
        estado_ips[ip] = ESTADOS[1]  # OK
    elif tiempo_respuesta < MAX_TIEMPO:
        estado_ips[ip] = ESTADOS[2]  # TARDE
    else:
        estado_ips[ip] = ESTADOS[3]  # DESCONECTADO

    return estado_ips[ip]  # Retornar el estado

# Función de petición a la IP
async def hacer_peticion(ip):
    inicio = time.time()

    # Llamada asincrónica a get_ip_lte_ssh
    valor_json_ip = await get_ip_lte_ssh(ip, ssh_script_c)

    delay = time.time() - inicio  # Tiempo de respuesta

    # Obtener marca de tiempo y estado
    # estado = obtener_marca_tiempo(ip, delay)
    if not valor_json_ip:
        valor_json_ip = {"estado": "DESCONECTADO"}
    else:
        valor_json_ip["estado"] = "OK"
        

    valor_json_ip["ip"] = ip
    valor_json_ip["tiempo_ejecucion"] = delay

    return {ip : valor_json_ip}


