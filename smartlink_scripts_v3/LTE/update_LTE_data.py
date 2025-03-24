## Smartlink - Captura de datos de equipos LTE
## Version      : V2025.2
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128
## Tables       : LTE_data

import sys
sys.path.append('/usr/smartlink')

# - - - - - - Models  - - - - - - -
from api_sql.fastapi.models.LTE_data_models         import LTE as Model
from api_sql.fastapi.models.ubicacion_gps_models    import UbicacionGPS
# - - - - - - - - - - - - - - - - -
from concurrent.futures import ThreadPoolExecutor
from datetime   import datetime
from globalHCG  import *
from LTE_module import *

import queue
import os
from pprint import pprint

# Local folder data
script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Parametros globales para LTE
TIPO            = "LTE"
MAX_CONCURRENTS = 25
log_file        = os.path.join(FOLDER_OUTPUT, f"{TIPO}_data.csv")
URL_GPS_LIST    = DB_API_URL + "ubicacion_gps/add_list"
URL_MODEL_LIST  = DB_API_URL + f"{TIPO}_data/add_list"

#paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)

## Funciones personzalidas
def async_task(ip_device, queue : queue.Queue):
    data_ssh    = getSshData(ip_device, _user = USER_SSH_MIKROTIK, _pass = PASS_SSH_MIKROTIK)
    data_snmp   = getSnmpData(ip_device, timeout = 5)

    if not data_ssh:
        return

    if False:
        print(f"\n -> {ip_device}")
        #print(f"Data SSH =")
        pprint(data_ssh)
        #print(f"Data SNMP =")
        pprint(data_snmp)
    
    hora_de_consulta        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mapeo_claves_sistema    = {
        0: ['name', 'type', 'APN', 'manufacturer', 'model', 'IMEI', 'IMSI'],  # Claves a buscar en diccionario_fuente_1
        1: ['sysUptime', 'sysName']  # Claves a buscar en diccionario_fuente_2
    }
    mapeo_claves_estado     = {
        0: ['status', 'network-mode', 'rssi', 'rsrq', 'rsrp', 'current-operator', 'lac', 'current-cellid', 'enb-id', 'sector-id'],  # Claves a buscar en diccionario_fuente_1
        1: []  # Claves a buscar en diccionario_fuente_2
    }

    dictionary_sistema  = extraer_claves([data_ssh, data_snmp], mapeo_claves_sistema)
    dictionary_enlaces  = extraer_indices_dictionary(data_snmp)
    dictionary_estado   = extraer_claves([data_ssh, data_snmp], mapeo_claves_estado)
    model_dictionary = {
        "ip"        : ip_device,
        "fecha"     : hora_de_consulta,
        "sistema"   : dictionary_sistema,
        "enlaces"   : list(dictionary_enlaces.values()),
        "estado"    : dictionary_estado 
    }

    list_gps_keys       = ["latitud", "longitud", "altura"]
    dictionary_gps      = {}
    for gps_key in list_gps_keys:
        if gps_key in data_ssh.keys():
            dictionary_gps[gps_key] = data_ssh[gps_key]

    queue.put([model_dictionary, dictionary_gps])


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos tipo LTE de la API
    url_inventario      = DB_API_URL + f"inventario/get"
    filter_inventario   = ["tipo", TIPO]
    subscribers         = [ item["ip"] for item in get_request_to_url_with_filters(url_inventario, filtrer_array = filter_inventario) ]
    print(f"Se han detectado un total de {len(subscribers)} equipos tipo Servidor en Inventario")

    q = queue.Queue()
    list_groups_ip_to_request = group_ips(subscribers, max_group_size = MAX_CONCURRENTS)
    
    list_groups_ip_to_request = group_ips(subscribers, max_group_size = MAX_CONCURRENTS)
    once = True

    with ThreadPoolExecutor(MAX_CONCURRENTS) as executor:
        for _group in list_groups_ip_to_request:
            futures = [executor.submit(async_task, _ip, q) for _ip in _group]
            
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()

            # Procesar los resultados inmediatamente
            model_array_list, gps_array_list = [], []
            while not q.empty():
                json_data, gps_json_data   = q.get()
                model_array_list.append(Model(**json_data))
                if gps_json_data:
                    gps_json_data["ip"]     = json_data["ip"]
                    gps_json_data["fecha"]  = json_data["fecha"]
                    gps_array_list.append(UbicacionGPS(**gps_json_data))

            if model_array_list:
                if once:
                    restart_log_file(log_file, Model)
                    once = False
                post_request_to_url_model_array(URL_MODEL_LIST, array_model_to_post = model_array_list)
                write_log_files(log_file, model_array_list)

            if gps_array_list:
                post_request_to_url_model_array(URL_GPS_LIST, array_model_to_post = gps_array_list)

except Exception as e:
    if str(e):
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
        #print(f" > Error Details:\n")
        #print(traceback.format_exc())





