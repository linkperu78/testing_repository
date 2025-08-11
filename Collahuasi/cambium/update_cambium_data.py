# =============================================================================
#                   Smartlink - Captura de datos de Cambium
# =============================================================================
#  Versión       : V2025.4
#  Autor         : HCG-Group, Área de Backend
#  Contacto      : Anexo 3128
#  Tablas        : ubicacion_gps, cambium_data
# =============================================================================
from smartlink.models.cambium_data_models  import CambiumData as Model
from smartlink.models.ubicacion_gps_models import UbicacionGPS
from concurrent.futures     import ThreadPoolExecutor
from smartlink.error_utils  import KEYNAME_ERROR_DICT, multiple_storage_errors, LOCAL_DB_ERROR
from smartlink.global_utils import FOLDER_OUTPUT, group_ips, get_my_server_ip
from smartlink.http_utils   import DB_API_URL, get_request_to_url, get_request_to_url_with_filters, post_request_to_url_model_array
from smartlink.csv_utils    import restart_log_file, write_log_files
from smartlink.json_utils   import load_json_to_dict
from smartlink.snmp_utils   import mySNMPClient
from datetime               import datetime
import traceback
import argparse
import queue
import re
import os

script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)
oid_folder      = os.path.join(script_folder, "snmp_json")

MARCA               = "cambium"
SNMP_TIMEOUT        = 5
DB_INVENTARIO_URL   = DB_API_URL + "inventario/get"
DB_SNMP_CONF_URL    = DB_API_URL + "snmp_conf/get_list_id/"
URL_POST_MODEL      = DB_API_URL + f"{MARCA}_data/add_list"
URL_POST_GPS        = DB_API_URL + "ubicacion_gps/add_list"

## Direccion de archivos de salida en /usr/smartlink/outputs
log_file            = os.path.join(FOLDER_OUTPUT, f"{MARCA}_data.csv")

## Activacion del modo DEBUG
_DEBUG_MODE = False
parser = argparse.ArgumentParser(description = "Script para almacenar datos de un equipo CAMBIUM en MariaDB usando la API")
parser.add_argument('-d', '--debug', action='store_true', help='Habilita el modo DEBUG (mensajes para diagnosticar)')
args = parser.parse_args()
_DEBUG_MODE = args.debug

## Carga de los diccionarios para mapear OID's
dict_PMPAP = load_json_to_dict( os.path.join(oid_folder, "PMPAP_versionNNNN.json") )
dict_PMPSM = load_json_to_dict( os.path.join(oid_folder, "PMPSM_versionNNNN.json") )
global_error_array = []

''' -------------------------------------------------------------------------- '''
## Tarea asincrona para manejar multiples en pararelo
def async_task(ip_device : str, tipo_PMP: str, queue : queue.Queue, dict_snmp : dict = None):
    agent_ip_snmp = mySNMPClient(
        ip_target   = ip_device,
        timeout     = SNMP_TIMEOUT,
        debug_mode  = _DEBUG_MODE
    )
    # Actualizamos acorde a las credenciales snmp
    agent_ip_snmp.update_credentials(dict_snmp)    
    
    oid_dict = {}
    if "-AP" in tipo_PMP:
        oid_dict = dict_PMPAP.copy()
    elif "-SM" in tipo_PMP:
        oid_dict = dict_PMPSM.copy()

    data_snmp_raw   = agent_ip_snmp.mapping_OID_dict(oid_dict, list)  # Si no hay valor, None
    fecha_device    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg       = data_snmp_raw.pop(KEYNAME_ERROR_DICT, None)
    if error_msg:
        error_msg   = [ip_device, fecha_device, error_msg]
    
    if not data_snmp_raw:
        if _DEBUG_MODE:
            print(f"No se pudo extraer datos de {ip_device} / {dict_snmp}")
        if error_msg:
            queue.put( [{}, {}, error_msg] )
        return 
    

    # Agregamos los campos iniciales
    data_snmp       = {
        "ip"    : ip_device,
        "fecha" : fecha_device
    }

    ## Avg power rx/tx
    message_avg_power = data_snmp_raw["avg_power"]
    if "-AP" in tipo_PMP:
        data_snmp["avg_power"] = {
            "tx" : float(message_avg_power)
        }
    else:
        matches = [float(m) for m in re.findall(r"(-?\d+\.\d+)\s*dBm\s*[VH]", message_avg_power)] if message_avg_power else [0,0]
        data_snmp["avg_power"] = {
            "rx" : matches[0] if len(matches) > 0 else None,
            "tx" : matches[1] if len(matches) > 1 else None
        }

    data_snmp["link_radio"] = {
        "tx" : data_snmp_raw["link_radio_tx"],
        "rx" : data_snmp_raw["link_radio_rx"],
    }

    data_snmp["snr"] = {
        "V" : data_snmp_raw["snr_v"],
        "H" : data_snmp_raw["snr_h"],
    }

    # Agregamos campos pendientes
    array_filtrado = [
        key for key in data_snmp_raw 
        if "GPS" not in key.upper() and not any(key.startswith(existing_key) for existing_key in data_snmp)
    ] 
    extra_dictionary = {key: data_snmp_raw[key] for key in array_filtrado}
    data_snmp["ifresults_metricas"] = extra_dictionary or None

    # Creamos el diccionario para datos GPS
    latitud  = float(data_snmp_raw.get("GPSLat", "0").replace('+', '').strip() or 0)
    longitud = float(data_snmp_raw.get("GPSLon", "0").replace('+', '').strip() or 0)
    altitud  = float(data_snmp_raw.get("GPSAlt", "0").strip() or 0)
    dictionary_gps = {
        "ip"        : ip_device,
        "fecha"     : fecha_device,
        "latitud"   : latitud,
        "longitud"  : longitud,
        "altitud"   : altitud
    } if latitud and longitud else {}

    queue.put([data_snmp, dictionary_gps, error_msg])


''' ------------------------------------------------------------------------------
---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
------------------------------------------------------------------------------ '''
try:
    ## Obtenemos datos de la lista de equipos RAJANT de la API
    filter_suscr    = ["marca", MARCA]
    raw_inventory   = get_request_to_url_with_filters(DB_INVENTARIO_URL, filter_array = filter_suscr)
    subscribers     = [ [row["ip"], row["snmp_conf"], row["tipo"] ] for row in raw_inventory]

    # Chequeamos el numero de equipos Cambiumm detectados
    num_cambium     = len( subscribers )
    if num_cambium  == 0:
        raise Exception("No hay equipos Cambium registrados")
    print(f"Se han detectado un total de {num_cambium} equipos Cambium / PMP-AP en Inventario")

    # Obtenemos la configuracion en forma de diccionario:
    config_snmp_unicos  = list(set(device[1] for device in subscribers))
    params              = {"index": config_snmp_unicos}

    snmp_config_dict    = get_request_to_url(DB_SNMP_CONF_URL, optional_param = params)
    config_dict         = {cfg.pop("id"): cfg for cfg in snmp_config_dict}
    subscribers         = [ [_ip, _tipo, config_dict.get(_index, {})] for _ip, _index, _tipo in subscribers]

    if _DEBUG_MODE: 
        for suscriptor in subscribers: print(suscriptor)

    q = queue.Queue()
    max_threads_number = 25
    list_groups_ip_to_request = group_ips(subscribers, max_group_size = max_threads_number)
    once = True
    total_groups = len(list_groups_ip_to_request)
    counter = 0

    with ThreadPoolExecutor(max_threads_number) as executor:
        for _group in list_groups_ip_to_request:
            counter += 1
            print(f"Procesando grupo N° {counter} ... de {total_groups}")
            futures = [executor.submit(async_task, _ip, _tipo, q, _conf_snmp) for _ip, _tipo, _conf_snmp in _group]
            
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()

            # Procesar los resultados inmediatamente
            model_array_list, gps_array_list = [], []

            while not q.empty():
                model_dict, gps_dict, error_message = q.get()
                if model_dict:
                    model_array_list.append( Model(**model_dict) )
                    if _DEBUG_MODE:
                        print(f"\n♦ ♦\n{model_dict}")
                if gps_dict:
                    gps_array_list.append( UbicacionGPS(**gps_dict) )
                if error_message:
                    global_error_array.append(error_message)

            if model_array_list:
                if once:
                    once = False
                    restart_log_file(log_file, Model)
                post_request_to_url_model_array(URL_POST_MODEL, array_model_to_post = model_array_list)
                write_log_files(log_file, model_array_list)

            if gps_array_list:
                post_request_to_url_model_array(URL_POST_GPS, array_model_to_post = gps_array_list)

    ## -----------Final del ThreadPoolExecutor -------------- ##
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
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
        try:
            my_ip = get_my_server_ip()
            fecha_device    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            global_error_array = [[my_ip, fecha_device, str(e)]]
            multiple_storage_errors(global_error_array)
        except Exception as e:
            if str(e):
                print(f"Error al guardar los fallos en {MARCA} : {e}")
                
    if _DEBUG_MODE:
        print(traceback.format_exc())

finally:
    print(f"Tarea finalizada. Se pueden revisar los valores en la BD o en {log_file}")


