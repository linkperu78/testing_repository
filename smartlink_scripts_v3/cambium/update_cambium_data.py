## Smartlink - Captura de datos de Instamesh/Rajant
## Version      : V2025.2
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128
## Tables       : ubicacion_gps, cambium_data

import sys
sys.path.append('/usr/smartlink')
from api_sql.fastapi.models.cambium_data_models     import CambiumData as Model
from api_sql.fastapi.models.ubicacion_gps_models    import UbicacionGPS
from concurrent.futures import ThreadPoolExecutor
from globalHCG  import *
from datetime   import datetime
from pprint     import pprint
import queue
import re
import os

script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Direccion de archivos de salida en /usr/smartlink/outputs
MARCA               = "cambium"
SNMP_TIMEOUT        = 10
DB_INVENTARIO_URL   = DB_API_URL + "inventario/get"
DB_SNMP_CONF_URL    = DB_API_URL + "snmp_conf/get_list_id/"
URL_POST_MODEL      = DB_API_URL + f"{MARCA}_data/add_list"
URL_POST_GPS        = DB_API_URL + "ubicacion_gps/add_list"

log_file            = os.path.join(FOLDER_OUTPUT, f"{MARCA}_data.csv")

# Diccionario SNMP:
if True:
    snmp_cambium_V1 = [
        ["GPSLat" , ".1.3.6.1.4.1.161.19.3.3.2.88"],            # 0
        ["GPSLon" , ".1.3.6.1.4.1.161.19.3.3.2.89"],            # 1
        ["GPSAlt" , ".1.3.6.1.4.1.161.19.3.3.2.90"],            # 2
        ["avg_power" , ".1.3.6.1.4.1.161.19.3.3.2.23"],         # 3
        ["link_radio_rx" , ".1.3.6.1.4.1.161.19.3.1.4.1.88"],   # 4
        ["link_radio_tx" , ".1.3.6.1.4.1.161.19.3.1.4.1.87"],   # 5
        ["inthroughputbytes" , ".1.3.6.1.2.1.2.2.1.10.1"],      # 6
        ["snr_v" , ".1.3.6.1.4.1.161.19.3.1.4.1.74"],           # 7
        ["snr_h" , ".1.3.6.1.4.1.161.19.3.1.4.1.84"]            # 8
    ]
    snmp_cambium_V2 = [
        ["GPSLat" , ".1.3.6.1.4.1.161.19.3.3.2.88"],            # 0
        ["GPSLon" , ".1.3.6.1.4.1.161.19.3.3.2.89"],            # 1
        ["GPSAlt" , ".1.3.6.1.4.1.161.19.3.3.2.90"],            # 2
        ["avg_power" , ".1.3.6.1.4.1.161.19.3.2.2.142"],        # 3
        ["link_radio_rx" , ".1.3.6.1.4.1.161.19.3.2.2.118"],    # 4
        ["link_radio_tx" , ".1.3.6.1.4.1.161.19.3.2.2.117"],    # 5
        ["inthroughputbytes" , ".1.3.6.1.2.1.2.2.1.10.1"],      # 6
        ["snr_v" , ".1.3.6.1.4.1.161.19.3.2.2.94"],             # 7
        ["snr_h" , ".1.3.6.1.4.1.161.19.3.2.2.106"]             # 8
    ]
else:
    snmp_cambiumV1 = [
        ["GPSLat"    , ".1.3.6.1.4.1.161.19.3.3.2.88.0"],                       # 0
        ["GPSLon"    , ".1.3.6.1.4.1.161.19.3.3.2.89.0"],                       # 1
        ["GPSAlt"    , ".1.3.6.1.4.1.161.19.3.3.2.90.0"],                       # 2
        ["avgpower"  , ".1.3.6.1.4.1.161.19.3.2.2.54.0"],                       # 3
        ["linkradiovert"     , ".1.3.6.1.4.1.161.19.3.2.2.118.0"],              # 4
        ["linkradiohoriz"    , ".1.3.6.1.4.1.161.19.3.2.2.117.0"],              # 5
        ["inthroughputbytes" , ".1.3.6.1.2.1.2.2.1.10.0"],                      # 6
        ["signaltonoiseratiovertical"    , ".1.3.6.1.4.1.161.19.3.2.2.94.0"],   # 7
        ["signaltonoiseratiohorizontal"  , ".1.3.6.1.4.1.161.19.3.2.2.105.0"]   # 8
    ]


''' Funciones personzalidas '''
## Obtener datos SNMP a partir de una lista
def easy_float_array_to_float(data_no_float):
    if not data_no_float:
        return None
    elif isinstance(data_no_float, str):
        return float(data_no_float)
        #data_snmp["link_radio_tx"] = float(msg_tx)
    else:
        return [float(a) for a in data_no_float]


def GetCambiumDataByIP(target_ip, dict_snmp, cambium_type):
    snmp_dict = {}
    snmp_cambium = []
    values_exists = False

    if "-AP" in cambium_type:
        #print(f"Evaluando Cambium AP / {target_ip}")
        snmp_cambium = snmp_cambium_V1
    elif "-SM" in cambium_type:
        #print(f"Evaluando Cambium SM / {target_ip}")
        snmp_cambium = snmp_cambium_V2

    for oid_name, oid in snmp_cambium:
        # Constructing the snmpbulkwalk command
        oid_result = snmp_request(oid, target_ip, dict_snmp, SNMP_TIMEOUT)
        if oid_result == -1:
            break

        if oid_result is None:
            snmp_dict[oid_name] = None
            continue

        values_exists = True
        if isinstance(oid_result, dict):
            snmp_dict[oid_name] = list(oid_result.values())     # Multiple values
        else:
            snmp_dict[oid_name] = oid_result    # Single values

    if values_exists:
        snmp_dict["ip"]     = target_ip
        snmp_dict["fecha"]  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return snmp_dict


def async_task(ip_device : str, tipo_PMP: str, queue : queue.Queue, dict_snmp : dict = None):
    data_snmp_raw   = GetCambiumDataByIP(ip_device, dict_snmp, tipo_PMP)
    #print(f"{data_snmp_raw}")
    if not data_snmp_raw:
        return
    
    # Agregamos los campos iniciales
    fecha_device    = data_snmp_raw["fecha"]
    data_snmp       = {
        "ip"    : ip_device,
        "fecha" : fecha_device
    }

    # Avg power rx/tx
    message_avg_power = data_snmp_raw["avg_power"].strip()
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
        "tx" : easy_float_array_to_float( data_snmp_raw["link_radio_tx"] ),
        "rx" : easy_float_array_to_float( data_snmp_raw["link_radio_rx"] ),
    }

    data_snmp["snr"] = {
        "V" : easy_float_array_to_float( data_snmp_raw["snr_v"] ),
        "H" : easy_float_array_to_float( data_snmp_raw["snr_h"] ),
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

    queue.put([data_snmp, dictionary_gps])


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos RAJANT de la API
    filter_inventario   = ["marca", MARCA]
    # Example: [ ["192.168.2.63", "public"], ... ]
    raw_inventory   = get_request_to_url_with_filters(DB_INVENTARIO_URL, filtrer_array = filter_inventario)
    subscribers     = [ [row["ip"], row["snmp_conf"], row["tipo"] ] for row in raw_inventory]
    #subscribers     = [ [row["ip"], row["snmp_conf"]] for row in raw_inventory if row["tipo"] == "PMP-AP"]

    # Chequeamos el numero de equipos Cambiumm detectados
    num_cambium     = len( subscribers )
    if num_cambium  == 0:
        raise Exception("No hay equipos Cambium registrados")
    print(f"Se han detectado un total de {num_cambium} equipos Cambium / PMP-AP en Inventario")

    #raise Exception()

    # Obtenemos la configuracion en forma de diccionario:
    config_snmp_unicos  = list(set(device[1] for device in subscribers))
    params              = {"index": config_snmp_unicos}

    snmp_config_dict    = get_request_to_url(DB_SNMP_CONF_URL, optional_param = params)
    config_dict         = {cfg.pop("id"): cfg for cfg in snmp_config_dict}
    subscribers         = [ [_ip, _tipo, config_dict.get(_index, {})] for _ip, _index, _tipo in subscribers]

    #for suscriptor in subscribers:
        #print(suscriptor)

    q = queue.Queue()
    max_threads_number = 25
    list_groups_ip_to_request = group_ips(subscribers, max_group_size = max_threads_number)
    once = True

    with ThreadPoolExecutor(max_threads_number) as executor:
        for _group in list_groups_ip_to_request:
            futures = [executor.submit(async_task, _ip, _tipo, q, _conf_snmp) for _ip, _tipo, _conf_snmp in _group]
            
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()

            # Procesar los resultados inmediatamente
            model_array_list, gps_array_list = [], []

            while not q.empty():
                model_dict, gps_dict = q.get()
                #pprint(model_dict)
                
                model_array_list.append( Model(**model_dict) )
                if gps_dict:
                    #pprint(gps_dict)
                    gps_array_list.append( UbicacionGPS(**gps_dict) )

        if model_array_list:
            if once:
                once = False
                restart_log_file(log_file, Model)
            post_request_to_url_model_array(URL_POST_MODEL, array_model_to_post = model_array_list)
            write_log_files(log_file, model_array_list)

        if gps_array_list:
            post_request_to_url_model_array(URL_POST_GPS, array_model_to_post = gps_array_list)
            pass

except Exception as e:
    if str(e):
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
    #print(" > Error Details:")
    #print(traceback.format_exc())










