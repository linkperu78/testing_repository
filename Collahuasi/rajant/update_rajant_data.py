# =============================================================================
#                   Smartlink - Captura de datos de Rajant
# =============================================================================
#  Versión       : V2025.4
#  Autor         : HCG-Group, Área de Backend
#  Contacto      : Anexo 3128
#  Tablas        : rajant_data, sensores, ubicacion_gps
# =============================================================================
from smartlink.models.rajant_data_models    import RajantData       as Model
from smartlink.models.ubicacion_gps_models  import UbicacionGPS
from smartlink.models.sensores_models       import Sensor

from concurrent.futures         import ThreadPoolExecutor
from datetime                   import datetime
from smartlink.error_utils      import multiple_storage_errors
from smartlink.global_utils     import FOLDER_OUTPUT, group_ips
from smartlink.http_utils       import DB_API_URL, get_request_to_url_with_filters, post_request_to_url_model_array
from smartlink.csv_utils        import restart_log_file, write_log_files
from bcapi_utils                import getRajantData, _PASSWORDS, _ROLES
from format_utils               import extract_rajant_model_data
import traceback
import time
import argparse
import queue
import os

script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Direccion de archivos de salida en /usr/smartlink/outputs
log_file        = os.path.join(FOLDER_OUTPUT, "rajant_data.csv")
log_sensores    = os.path.join(FOLDER_OUTPUT, "sensores.csv")

# Constantes
MARCA           = "rajant"
DEFAULT_ROL     = "view"
URL_GPS_LIST    = DB_API_URL + "ubicacion_gps/add_list"
URL_SENSOR_LIST = DB_API_URL + "sensores/add_list"
URL_RAJANT_LIST = DB_API_URL + "rajant_data/add_list"

## Activacion del modo DEBUG
_DEBUG_MODE = False
parser = argparse.ArgumentParser(description="Script SNMP async handler")
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()
_DEBUG_MODE = args.debug


def async_task(ip, queue : queue.Queue):
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        data_rajant = getRajantData(ipv4    = ip, 
                                    user    = _ROLES[DEFAULT_ROL], 
                                    passw   = _PASSWORDS[DEFAULT_ROL],
                                    timeout = 5, 
                                    debug_mode = _DEBUG_MODE)
        if data_rajant is None:
            return
        
        if _DEBUG_MODE and queue.empty():
            print(f" -> {ip}:\n{data_rajant}\n\n")

        rajant_dict, array_cost_master = extract_rajant_model_data(data_rajant)
        if rajant_dict:
            queue.put([rajant_dict, array_cost_master, ip, current_date, ""])
    except Exception as e:
        queue.put( [{}, [], ip, current_date, str(e)] )


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos RAJANT de la API
    url_inventario      = DB_API_URL + f"inventario/get"
    filter_inventario   = ["marca", MARCA]
    subscribers         = [ item["ip"] for item in get_request_to_url_with_filters(url_inventario, filter_array = filter_inventario) ]
    print(f"Se han detectado un total de {len(subscribers)} equipos en Inventario")

    q = queue.Queue()
    max_threads_number = 25

    list_groups_ip_to_request = group_ips(subscribers, max_group_size = max_threads_number)
    total_groups    = len(list_groups_ip_to_request)
    counter         = 1
    with ThreadPoolExecutor(max_threads_number) as executor:
        for counter, _group in enumerate(list_groups_ip_to_request, 1):
            print(f"♦ Procesando grupo {counter} de {total_groups}...")
            futures = [executor.submit(async_task, _ip, q) for _ip in _group]
            for future in futures:
                future.result()
            time.sleep(2)

    # Procesamos los datos obtenidos de Rajant async_task
    print(f" • Guardando los datos en la base de datos")

    dictionary_ip_data = {}
    dictionary_cost_master = {}
    global_error_array = []
    while not q.empty():    
        _rajant_data, _wired_array_cost, ip_device, current_date, error_message  = q.get()
        if error_message:
            global_error_array.append([ip_device, current_date, error_message])
        if _wired_array_cost:
            for ip_cost_master, value_cost_master in _wired_array_cost:
                dictionary_cost_master[ip_cost_master] = value_cost_master
        if _rajant_data:
            dictionary_ip_data[ip_device] = {
                **_rajant_data,
                'fecha' : current_date
            }

    if _DEBUG_MODE:
        print(f"-> Diccionario obtenido de costos hacia maestro:\n{dictionary_cost_master}")
        
    # Update wired costs
    for ip_device, cost_device in dictionary_cost_master.items():
        if ip_device in dictionary_ip_data and "wired" in dictionary_ip_data[ip_device]:
            dictionary_ip_data[ip_device]["wired"]["cost"] = cost_device

    # Send data to MariaDB
    model_array_list, sensores_array_list, gps_array_list = [], [], []
    for ip_device, ip_dictionary in dictionary_ip_data.items():
        fecha_ip = ip_dictionary["fecha"]
        
        if _DEBUG_MODE:
            print(f"- Procesando {ip_device} ...")

        # rajant_dictionary = [gps, sensores, config, instamesh, wired, wireless]
        model_array_list.append(
            Model(
                ip          = ip_device,
                fecha       = fecha_ip,
                config      = ip_dictionary.get("config", {}),
                instamesh   = ip_dictionary.get("instamesh", {}),
                wired       = ip_dictionary.get("wired", {}),
                wireless    = ip_dictionary.get("wireless", {})
            )
        )

        if "sensores" in ip_dictionary:
            sensores_array_list.append(Sensor(
                ip=ip_device,
                fecha=fecha_ip,
                **ip_dictionary["sensores"]
            ))

        if "gps" in ip_dictionary:
            gps_array_list.append(UbicacionGPS(
                ip=ip_device,
                fecha=fecha_ip,
                **ip_dictionary["gps"]
            ))

    if model_array_list:
        post_request_to_url_model_array(URL_RAJANT_LIST, 
                                        array_model_to_post = model_array_list,
                                        _debug = _DEBUG_MODE)
        restart_log_file(log_file, Model)
        write_log_files(log_file, model_array_list)

    if gps_array_list:
        post_request_to_url_model_array(URL_GPS_LIST, 
                                        array_model_to_post = gps_array_list,
                                        _debug = _DEBUG_MODE)

    if sensores_array_list:
        post_request_to_url_model_array(URL_SENSOR_LIST, 
                                        array_model_to_post = sensores_array_list,
                                        _debug = _DEBUG_MODE)
        restart_log_file(log_sensores, Sensor)
        write_log_files(log_sensores, sensores_array_list)

    try:
        if global_error_array:
            print(f"\n\n - - - - - - - - Procesando errores encontrados durante la ejecucion - - - - - - - - ")
            counter = 0
            for error_message in global_error_array:
                counter += 1
                print(f"Error {counter} = {error_message}")
            multiple_storage_errors(global_error_array)
    except Exception as e:
        if str(e):
            print(f"Error al guardar los fallos en {MARCA} : {e}")

except Exception as e:
    if str(e):
        print(f" !! {script_folder} main function error: {e}")
        if _DEBUG_MODE:
            print(" > Error Details:")
            print(traceback.format_exc())











