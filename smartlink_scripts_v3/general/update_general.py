## Smartlink - Captura de datos de latencia
## Version      : V2025.2
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128
## Tables       : Latencia
import sys
sys.path.append('/usr/smartlink')
from api_sql.fastapi.models.latencia_models import Latencia as Model
from datetime   import datetime
from globalHCG  import *
from concurrent.futures import ThreadPoolExecutor

import subprocess
import traceback
import queue
import os

script_path         = os.path.abspath(__file__)
script_folder       = os.path.dirname(script_path)
script_name         = os.path.basename(script_path)

# Direccion de archivos de salida en /usr/smartlink/outputs
file_latency        = os.path.join(FOLDER_OUTPUT, "latency.csv")


##  ---------------------------    FUNCIONES     ---------------------------
def ping_host(host, _debug = False) -> float:
    try:
        # Ejecutar el comando `ping` del sistema
        result = subprocess.run(
            ['ping', '-c', '3', '-W', '0.5', host],  # -c 3: tres intentos, -W 1: timeout en segundos
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            # Parsear el tiempo promedio de RTT del resultado
            for line in result.stdout.splitlines():
                if "avg" in line:  # Buscar la línea con estadística (summary)
                    return float(line.split('=')[1].split('/')[1])  # Extraer el RTT promedio

        return -1 # Fallo en el ping

    except Exception as e:
        if _debug:
            print(f"Error running ping for {host}: {e}")
        return -1


def async_task(ip_host : str, queue : queue.Queue):
    # Realiza un ping asíncrono y guarda el resultado en la cola
    response_task = {
        "ip"        : ip_host,
        "latencia"  : ping_host(ip_host),
        "fecha"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    queue.put(response_task)


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos de la API
    url_inventario  = DB_API_URL + f"inventario/get"
    subscribers     = [item["ip"] for item in get_request_to_url(url_inventario)]
    print(f"Se han detectado un total de {len(subscribers)} equipos en Inventario")

    q = queue.Queue()
    max_threads_number = 25

    list_groups_ip_to_request = group_ips(subscribers, max_group_size = max_threads_number)
    once = True
    with ThreadPoolExecutor(max_threads_number) as executor:
        for _group in list_groups_ip_to_request:
            futures = [executor.submit(async_task, _ip, q) for _ip in _group]
            
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()

            # Procesar los resultados inmediatamente
            model_array_list = []
            while not q.empty():
                json_data = q.get()
                if json_data:
                    model_array_list.append(Model(**json_data))

            # Enviar datos en lotes a la base de datos
            if model_array_list:
                if once:
                    restart_log_file(file_latency, Model)
                    once = False
                post_request_to_url_model_array(DB_API_URL + "latencia/add_list", array_model_to_post = model_array_list)
                write_log_files(file_latency, model_array_list)

except Exception as e:
    if str(e):
        print(f"\n‼ Error en {script_name}:\n{e}")
        #print(" > Error Details:")
        #print(traceback.format_exc())



