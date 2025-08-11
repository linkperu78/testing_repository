# =============================================================================
#                   Smartlink - Captura de datos de latencia
# =============================================================================
#  Versión       : V2025.4
#  Autor         : HCG-Group, Área de Backend
#  Contacto      : Anexo 3128
#  Tablas        : latencia
# =============================================================================
from smartlink.models.latencia_models import Latencia as Model
from smartlink.global_utils import FOLDER_OUTPUT, group_ips, print_dictionary
from smartlink.http_utils   import DB_API_URL, get_request_to_url, post_request_to_url_model_array
from smartlink.csv_utils    import restart_log_file, write_log_files
from smartlink.local_utils  import ping_host, print_index_models_from_array
from concurrent.futures     import ThreadPoolExecutor
from datetime               import datetime

import argparse
import traceback
import queue
import os

MAX_THREAD_NUMBER   = 25
script_path         = os.path.abspath(__file__)
script_folder       = os.path.dirname(script_path)
script_name         = os.path.basename(script_path)

# Direccion de archivos de salida en /usr/smartlink/outputs
file_latency        = os.path.join(FOLDER_OUTPUT, "latency.csv")

## Activacion del modo DEBUG
_DEBUG_MODE = False
_TEST_MODE  = False
parser = argparse.ArgumentParser(description="Script SNMP async handler")
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
parser.add_argument('-t', '--test', action='store_true', help='Enable test environment')
args = parser.parse_args()
_DEBUG_MODE = args.debug
_TEST_MODE  = args.test


''' -------------------------------------------------------------------------- '''
def async_task(ip_host : str, queue : queue.Queue):
    # Realiza un ping asíncrono y guarda el resultado en la cola
    response_task = {
        "ip"        : ip_host,
        "latencia"  : ping_host(ip_host, _debug = _DEBUG_MODE),
        "fecha"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if _DEBUG_MODE:
        print_dictionary(response_task)
    
    queue.put(response_task)


''' ------------------------------------------------------------------------------
---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
------------------------------------------------------------------------------ '''
try:
    ## Obtenemos datos de la lista de equipos de la API
    url_inventario  = DB_API_URL + f"inventario/get"
    suscribers      = [item["ip"] for item in get_request_to_url(url_inventario)]
    print(f"Se han detectado un total de {len(suscribers)} equipos en Inventario")

    q = queue.Queue()
    max_threads_number = MAX_THREAD_NUMBER

    list_groups_ip_to_request   = group_ips(suscribers, max_group_size = max_threads_number)
    url_to_post_models_dict     = DB_API_URL + "latencia/add_list"
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
                model_data = q.get()
                if model_data:
                    model_array_list.append(Model(**model_data))

            # Enviar datos en lotes a la base de datos
            if model_array_list:
                try:
                    if not _TEST_MODE:
                        post_request_to_url_model_array(url_to_post_models_dict, 
                                                        array_model_to_post = model_array_list,
                                                        _debug = _DEBUG_MODE)
                    else:
                        len_models_available = len(model_array_list)
                        row_to_print = min(len_models_available, 5)
                        print_index_models_from_array(model_array_list, row_to_print)
                except Exception as e:
                    print(f"{script_name} | Error al tratar de enviar los datos por HTTP: {e}")
                    
                try:
                    if once:
                        restart_log_file(file_latency, Model)
                        once = False
                    write_log_files(file_latency, model_array_list)
                except Exception as e:
                    print(f"{script_name} | Error al tratar de almacenar el registro: {e}")
                
except Exception as e:
    if str(e):
        print(f"\n‼ Error en {script_name}:\n{e}")
        if _DEBUG_MODE:
            print(traceback.format_exc())



