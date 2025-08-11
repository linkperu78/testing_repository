from smartlink.http_utils import DB_API_URL
from LTE_module import USER_SSH_MIKROTIK, PASS_SSH_MIKROTIK, get_ip_lte_ssh
from time import time
import socket
import zmq
import requests
import asyncio
import os

# path
script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_ssh_name = "ssh_LTE_request"

# Ruta al programa compilado en C
#ssh_script_path = os.path.join("/usr/smartlink/LTE", script_ssh_name)
ssh_script_path = os.path.join(script_folder, script_ssh_name)

# Constantes
TIPO = "LTE"
ESTADOS = {
    1 : "OK",
    2 : "TARDE",
    3 : "DESCONECTADO"
}
INTERVALO_TIEMPO        = 5     # Segundos
INTERVALO_INVENTARIO    = 15    # Segundos
TOLERANCIA_INTERVALO    = INTERVALO_TIEMPO
MAX_TIEMPO_ESPERA       = 5 * INTERVALO_TIEMPO
TIMEOUT_API_REQUEST     = 1 * INTERVALO_TIEMPO
URL_API_INVENTARIO      = DB_API_URL + f"inventario/get/tipo/{TIPO}"

# Socket TCP - Configurar ZeroMQ Publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://localhost:5555")  # Escuchar en puerto 5555

# Estado de cada IP
dict_ip_status      = {}
dict_tareas_activas = {}

## Funcion para obtner la lista de equipos LTE en MariaDB
def get_inventario_LTE() -> list:
    ip_device = []
    request_inventario = requests.get(URL_API_INVENTARIO, timeout = TIMEOUT_API_REQUEST)

    if request_inventario.status_code == 200:
        inventario_data = request_inventario.json()
        ip_device = [record['ip'] for record in inventario_data]
    else:
        print(f"Failed to fetch data. {URL_API_INVENTARIO}\n- Status code: {request_inventario.status_code}")

    return ip_device


# Funcion de peticion a IP por SSH
async def hacer_peticion(ip):
    print(f"Evaluando {ip}:")
    valor_json_ip       = get_ip_lte_ssh(ip, 
                                         ssh_script_path,
                                         usuario    = USER_SSH_MIKROTIK,
                                         contraseña = PASS_SSH_MIKROTIK 
                                         #delay_max  = MAX_TIEMPO_ESPERA
                                         )

    print(f"- {valor_json_ip}")
    
    if not valor_json_ip:
        return valor_json_ip
    
    valor_json_ip["ip"] = ip

    
    return valor_json_ip


# Funcion de monitoreo de los datos obtenidos de cada IP
async def monitorear_ip(ip):
    """Ciclo individual de monitoreo para cada IP."""
    global dict_ip_status
    while True:
        inicio_marca    = time()
        data_json_ip    = await hacer_peticion(ip)
        tiempo_actual   = time()
        if data_json_ip:
            dict_ip_status[ip][1] = tiempo_actual

            print(f"- - {data_json_ip}\n - -")
            
            socket.send_json(data_json_ip)
        tiempo_transcurrido = tiempo_actual - inicio_marca
        if tiempo_transcurrido < INTERVALO_TIEMPO:
            await asyncio.sleep(INTERVALO_TIEMPO - tiempo_transcurrido)

## Imprimimos el estado de los equipos cada cierto tiempo
async def print_status_devices():
    global dict_ip_status
    while True:
        current_time = time()
        for ip, values in dict_ip_status.items():
            elapse_time = current_time - values[1]
            if elapse_time < INTERVALO_TIEMPO + TOLERANCIA_INTERVALO:
                values[0] = ESTADOS[1]
            elif elapse_time > MAX_TIEMPO_ESPERA:
                values[0] = ESTADOS[3]
            else:
                values[0] = ESTADOS[2]

        nuevo_dict = {ip: estado[0] for ip, estado in dict_ip_status.items()}
        #print(f"+{nuevo_dict}")
        socket.send_json(nuevo_dict)
        await asyncio.sleep(INTERVALO_TIEMPO)


# Actualizamos el inventario de los equipos
async def actualizar_lista_ips() -> None:
    global dict_ip_status, dict_tareas_activas

    while True:
        init_time       = time()
        lista_ips       = get_inventario_LTE()
        
        lista_ips_set   = set(lista_ips)  # Convierte a conjunto para O(1) en búsquedas
        #print(lista_ips_set)
        # 🔴 Primero eliminamos las IP que ya no estan
        list_ip_to_remove   = [ip for ip in dict_ip_status if ip not in lista_ips_set]
        for ip in list_ip_to_remove:
            if ip in dict_tareas_activas:
                dict_tareas_activas[ip].cancel()  # Cancela la tarea
                del dict_tareas_activas[ip]  # Elimina la referencia
            del dict_ip_status[ip]  # Elimina la IP del diccionario

        # 🟢 Agregamos los nuevos equipos encontrados, inicializando sus estados como ESTADOS[3]
        for ip in lista_ips:
            dict_ip_status.setdefault(ip, [ESTADOS[3], time() - MAX_TIEMPO_ESPERA])
            if ip not in dict_tareas_activas:  # Evita recrear tareas existentes
                dict_tareas_activas[ip] = asyncio.create_task(monitorear_ip(ip))
        elapse_time      = int(time() - init_time)
        #pprint(dict_ip_status)
        await asyncio.sleep( min(0, INTERVALO_INVENTARIO - elapse_time) )

## Pool de funciones asyncronicas
async def main():
    dict_tareas_activas["print_status"] = asyncio.create_task( print_status_devices() )
    await actualizar_lista_ips()

## PROGRAMA INICIAL
if __name__ == "__main__":
    asyncio.run(main())
