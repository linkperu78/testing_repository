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
import threading
import subprocess
import traceback
import queue
import re
import csv
import requests
import os

script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Direccion de archivos de salida en /usr/smartlink/outputs
MARCA               = "cambium"
DB_INVENTARIO_URL   = DB_API_URL + "inventario/get"
DB_SNMP_CONF_URL    = DB_API_URL + "snmp_conf/get_list_id/"
URL_POST_MODEL      = DB_API_URL + f"{MARCA}_data/add_list"
URL_POST_GPS        = DB_API_URL + "ubicacion_gps/add_list"

log_file            = os.path.join(FOLDER_OUTPUT, f"{MARCA}_data.csv")
SNMP_TIMEOUT        = 10

# Diccionario SNMP:
if True:
    snmp_cambium = [
        ["GPSLat" , ".1.3.6.1.4.1.161.19.3.3.2.88.0"],          # 0
        ["GPSLon" , ".1.3.6.1.4.1.161.19.3.3.2.89.0"],          # 1
        ["GPSAlt" , ".1.3.6.1.4.1.161.19.3.3.2.90.0"],          # 2
        ["avg_power" , ".1.3.6.1.4.1.161.19.3.2.2.142.0"],      # 3
        ["link_radio_rx" , ".1.3.6.1.4.1.161.19.3.2.2.118.0"],  # 4
        ["link_radio_tx" , ".1.3.6.1.4.1.161.19.3.2.2.117.0"],  # 5
        ["inthroughputbytes" , ".1.3.6.1.2.1.2.2.1.10.1"],      # 6
        ["snr_v" , ".1.3.6.1.4.1.161.19.3.2.2.94.0"],           # 7
        ["snr_h" , ".1.3.6.1.4.1.161.19.3.2.2.106.0"]           # 8
    ]
else:
    snmp_cambium = [
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

## Funciones personzalidas
def GetCambiumDataByIP(target_ip, community):
    snmp_dict = {}
    for oid_name, oid in snmp_cambium:        
        # Constructing the snmpbulkwalk command
        string_timeout = f"{SNMP_TIMEOUT}"
        command = [
            "snmpwalk",
            "-v", "2c",  # SNMP version (v2c in this case)
            "-c", community,  # SNMP community string
            "-O", "nq",  # Output format options (e.g., numeric OIDs, quiet)
            "-t", string_timeout,   
            target_ip,  # Target IP address
            oid  # The OID to walk
        ]
        try:
            # Running the snmpbulkwalk command
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout = SNMP_TIMEOUT + 2).stdout
            print(f"\nOriginal {oid_name}/{oid}:\n|{result}|")
            
            for line in result.splitlines():
                #print(f"Split = |{line}|")
                parts = line.split(" ", 1)  # Dividir en OID y valor
                if len(parts) == 2:
                    oid, value = parts
                    if "No Such Instance" in value:
                        snmp_dict[oid_name] = ""
                    else:
                        snmp_dict[oid_name] = value.strip()
        except subprocess.TimeoutExpired:
            break
            print(f"Timeout occurred while querying {target_ip} for {oid_name}.")
            #snmp_dict[oid_name] = "TIMEOUT"
        except subprocess.CalledProcessError as e:
            break
            print(f"Error performing SNMP walk for {oid_name}: {e.stderr}")

    if snmp_dict:
        snmp_dict["ip"]     = target_ip
        snmp_dict["fecha"]  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return snmp_dict


def async_task(ip_device : str, queue : queue.Queue, optional : dict = None):
    community   = optional["comunidad"]
    data_snmp   = GetCambiumDataByIP(ip_device, community)

    if not data_snmp:
        return

    #print(f"{data_snmp}")

    # Avg power rx/tx
    matches = [float(m) for m in re.findall(r"(-?\d+\.\d+)\s*dBm\s*[VH]", data_snmp["avg_power"])]
    data_snmp["avg_power_rx"] = matches[0] if len(matches) > 0 else -1
    data_snmp["avg_power_tx"] = matches[1] if len(matches) > 1 else -1

    msg_rx = data_snmp["link_radio_rx"]
    msg_tx = data_snmp["link_radio_tx"]
    data_snmp["link_radio_rx"]  = float(msg_rx.replace('"', '')) if msg_rx else -1
    data_snmp["link_radio_tx"]  = float(msg_tx.replace('"', '')) if msg_tx else -1

    ip_device       = data_snmp["ip"]
    fecha_device    = data_snmp["fecha"]
    # Creamos el diccionario para datos GPS
    latitud     = float( data_snmp["GPSLat"].replace('"', '').replace('+', '') )
    longitud    = float( data_snmp["GPSLon"].replace('"', '').replace('+', '') )
    altitud     = float( data_snmp["GPSAlt"] )

    dictionary_gps = {
        "ip"        : ip_device,
        "fecha"     : fecha_device,
        "latitud"   : latitud,
        "longitud"  : longitud,
        "altitud"   : altitud
    } if latitud != 0 and longitud != 0 else {}

    for a in ["GPSLat", "GPSLon", "GPSAlt", "avg_power"]:
        data_snmp.pop(a, None)  # Avoids KeyError if key is missing
    
    fieldnames          = list(Model.model_fields.keys()) + ["fecha", "ip"]
    extra_dictionary    = {k: v for k, v in data_snmp.items() if k not in fieldnames}
    data_snmp           = {k: v for k, v in data_snmp.items() if k in fieldnames}
    data_snmp["ifresults_metricas"] = extra_dictionary
    data_snmp["snr_h"] = data_snmp.get("snr_h", -1) or -1
    data_snmp["snr_v"] = data_snmp.get("snr_v", -1) or -1

    queue.put([data_snmp, dictionary_gps])


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos RAJANT de la API
    filter_inventario   = ["marca", MARCA]
    # Example: [ ["192.168.2.63", "public"], ... ]
    raw_inventory   = get_request_to_url_with_filters(DB_INVENTARIO_URL, filtrer_array = filter_inventario)
    subscribers     = [ [row["ip"], row["snmp_conf"]] for row in raw_inventory if row["tipo"] == "PMP-AP"]

    # Chequeamos el numero de equipos Cambiumm detectados
    num_cambium = len(subscribers)
    if num_cambium < 1 :
        raise Exception("No hay equipos Cambium registrados")
    print(f"Se han detectado un total de {num_cambium} equipos Cambium / PMP-AP en Inventario")


    # Obtenemos la configuracion en forma de diccionario:
    config_snmp_unicos  = list(set(device[1] for device in subscribers))
    params              = {"index": config_snmp_unicos}

    snmp_config_dict    = get_request_to_url(DB_SNMP_CONF_URL, optional_param = params)
    config_dict         = {cfg.pop("id"): cfg for cfg in snmp_config_dict}
    subscribers         = [ [_ip, config_dict[_index]] for _ip, _index in subscribers]

    q = queue.Queue()
    max_threads_number = 25
    list_groups_ip_to_request = group_ips(subscribers, max_group_size = max_threads_number)
    once = True

    with ThreadPoolExecutor(max_threads_number) as executor:
        for _group in list_groups_ip_to_request:
            futures = [executor.submit(async_task, _ip, q, _conf_snmp) for _ip, _conf_snmp in _group]
            
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()

            # Procesar los resultados inmediatamente
            model_array_list, gps_array_list = [], []

            while not q.empty():
                model_dict, gps_dict   = q.get()

                model_array_list.append( Model(**model_dict) )
                if gps_dict:
                    gps_array_list.append( UbicacionGPS(**gps_dict) )

        if model_array_list:
            if once:
                once = False
                restart_log_file(log_file, Model)
            post_request_to_url_model_array(URL_POST_MODEL, array_model_to_post = model_array_list)
            write_log_files(log_file, model_array_list)

        if gps_array_list:
            post_request_to_url_model_array(URL_POST_GPS, array_model_to_post = gps_array_list)
        

except Exception as e:
    if str(e):
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
    #print(" > Error Details:")
    #print(traceback.format_exc())











