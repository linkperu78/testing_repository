## Smartlink - Captura de datos de equipos LTE modo HITMAN
## Version      : V2025.2
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128

# - - - - - - - - - - - - - - - - -
import sys
sys.path.append('/usr/smartlink')

from LTE.LTE_module             import getSshData
from rajant.constants_rajant    import getRajantData, _HCG_RAJANT_USER, _HCG_RAJANT_PASS
from datetime                   import datetime
from globalHCG                  import *

import subprocess
import glob
import traceback
import os
import time
import asyncio

# Local folder data
script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Parametros globales para LTE
TIPO                = "LTE"
MAX_CONCURRENTS     = 10
DEBUG_MODE          = True
FOLDER_OUT_HITMAN   = os.path.join(FOLDER_HITMAN, TIPO)


## Funciones personzalidas
def ping_host(host) -> float:
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
        if DEBUG_MODE:
            print(f"Error running ping for {host}: {e}")
        return -1


## Funcion para obtener los datos GPS (si no hay, retorna None)
def getGPSData(ip_device_rajant : str, time_out : int = 5) -> dict | None:
    try:
        data_proto_rajant = getRajantData(
            ipv4 = ip_device_rajant, 
            user = _HCG_RAJANT_USER, passw = _HCG_RAJANT_PASS,
            timeout = time_out, debug_mode = DEBUG_MODE
        )
        if data_proto_rajant and data_proto_rajant.HasField("gps"):
            gps_altitud = float(data_proto_rajant.gps.gpsPos.gpsAlt)
            return {
                "gpsLat"    : dms_to_dd(data_proto_rajant.gps.gpsPos.gpsLat),
                "gpsLong"   : dms_to_dd(data_proto_rajant.gps.gpsPos.gpsLong),
                "gpsAlt"    : round(gps_altitud, 2),
            }
        
        return None
    
    except Exception as e:
        if DEBUG_MODE:
            print(f"✘ Error en \"getGPSData()\" function:\n{e}")
        return None
    

## Funcion en pararelo para cada equipo obtenido
async def async_task(row_ip, fq_sample, queue: asyncio.Queue):

    base_dictionary = {
        "name"              : "name",
        "type"              : "type",
        "APN"               : "apn-profiles",
        "manufacturer"      : "manufacturer",
        "model"             : "model",
        "IMEI"              : "IMEI",
        "IMSI"              : "IMSI",
        "status"            : "status",
        "networkmode"       : "network-mode",
        "rssi"              : "rssi",
        "rsrp"              : "rsrp",
        "rsrq"              : "rsrq",
        "snr"               : "sinr",
        "currentoperator"   : "current-operator",
        "lac"               : "lac",
        "currentcellid"     : "currentcell-id",
        "enbid"             : "enb-id",
        "sectorid"          : "sectorid",
        "linkdowns"         : "link-downs",
        "gpsLat"            : "latitud",
        "gpsLong"           : "longitud",
        "gpsAlt"            : "altura",
        #"accestechnology" : None,
        #"lastlinkdowntime" : None,
        #"lastlinkuptime" : None,
    }

    ip_device, ip_gps_reference = row_ip

    task_timeout = min(5, fq_sample -2)

    data_ssh = await asyncio.to_thread(getSshData, ip_device, _user=USER_SSH_MIKROTIK, _pass=PASS_SSH_MIKROTIK,
                                       timeout=task_timeout, _mode_debug=DEBUG_MODE)
    
    data_gps = await asyncio.to_thread(getGPSData, ip_gps_reference, 
                                       time_out=task_timeout - 1) if ip_gps_reference else None

    if not data_ssh and not data_gps:
        return

    ## Datos de LTE por SSH
    hora_de_consulta    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if data_ssh:
        data_ssh_lower      = {key.lower(): value for key, value in data_ssh.items()}
        dictionary_sistema  = {new_key: data_ssh_lower.get(original_key.lower(), None) 
                            for new_key, original_key in base_dictionary.items() }
        dictionary_sistema  = {
            key: (value.replace('"', '') if isinstance(value, str) else value)
            for key, value in dictionary_sistema.items()
        }

    if data_gps:
        dictionary_sistema.update(data_gps)

    dictionary_sistema["latencia"]  = ping_host(ip_device, _debug = DEBUG_MODE)
    dictionary_sistema["ip"]        = ip_device
    dictionary_sistema["fecha"]     = hora_de_consulta
    queue.put(dictionary_sistema)


## Proceso para manejar tareas asincronicas (en pararelo)
async def process_devices(ip_list, freq_muestreo):
    """Ejecuta todas las inspecciones en paralelo y guarda los resultados."""
    queue = asyncio.Queue()

    # Ejecutar todas las tareas en paralelo
    tasks = [async_task(row_ip, freq_muestreo, queue) for row_ip in ip_list]
    await asyncio.gather(*tasks)

    # Procesar resultados
    while not queue.empty():
        json_data = await queue.get()
        save_dictionary_to_csv(json_data)


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    if len(sys.argv) < 3:
        print("Uso: python script.py <tiempo_duracion_min> <intervalo_seg>")
        sys.exit(1)
    
    tiempo_duracion_min     = int(sys.argv[1])
    intervalo_seg           = int(sys.argv[2])

    ## Obtenemos datos de la lista de equipos tipo LTE de la API
    url_inventario      = DB_API_URL + f"inventario/get"
    filter_inventario   = ["tipo", TIPO]
    
    subscribers = [
        [item["ip"], anotacion_dict.get("gps")]
        for item in get_request_to_url_with_filters(url_inventario, filtrer_array=filter_inventario)
        if item.get("anotacion") 
        and isinstance(item["anotacion"], str)  # Ensure it's a string before parsing
        and "modo" in (anotacion_dict := json.loads(item["anotacion"]))  # Parse JSON safely
        and anotacion_dict["modo"] == "heatmap"
    ]

    if len(subscribers) == 0:
        print(f"No hay equipos compatibles con LTE / Hitman")
        raise Exception()

    # Crear la carpeta si no existe
    if not os.path.exists(FOLDER_OUT_HITMAN):
        os.makedirs(FOLDER_OUT_HITMAN)
    # Si hay archivos ya scaneados, se eliminaran
    else:
        for file in glob.glob(os.path.join(FOLDER_OUT_HITMAN, "*.csv")):
            os.remove(file)

    total_iterations = tiempo_duracion_min * 60 // intervalo_seg
    
    iteration = 0
    tiempo_finalizacion     = time.time() + tiempo_duracion_min * 60
    print(f"Progreso: 0% | Total = {tiempo_duracion_min} min | Intervalo = {intervalo_seg} s")
    while time.time() < tiempo_finalizacion:
        current_time = time.time()
        asyncio.run(process_devices(subscribers, intervalo_seg))
        
        elapsed_time = time.time() - current_time
        sleep_time = max(0, intervalo_seg - elapsed_time)
        time.sleep(sleep_time)
        
        iteration += 1
        progress = (iteration / total_iterations) * 100
        print(f"Progreso: {progress:.2f}%")

except Exception as e:
    if str(e):
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
        #print(f" > Error Details:\n")
        #print(traceback.format_exc())