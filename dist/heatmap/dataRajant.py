## Smartlink - Captura de datos de equipos RAJANT modo HITMAN
## Version      : V2025.2
## Author       : HCG-GROUP, Area de Backend
## Contacto     : Anexo 3128

# - - - - - - - - - - - - - - - - -
import sys
sys.path.append('/usr/smartlink')

from rajant.bcapi_utils     import getRajantData, _ROLES, _PASSWORDS
from rajant.format_utils    import dms_to_dd
# - - - - - - - - - - - - - - - - -
from smartlink.local_utils  import ping_host
from smartlink.global_utils import FOLDER_HITMAN
from smartlink.http_utils   import DB_API_URL, get_request_to_url, get_request_to_url_with_filters
from datetime import datetime
import asyncio
import time
import json
import glob
import shutil
import os
import csv

# Local folder data
script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Parametros globales para LTE
VERSION             = "Rajant"
DEFAULT_ROL         = "co"
MAX_CONCURRENTS     = 10
DEBUG_MODE          = False
FOLDER_OUT_HITMAN   = os.path.join(FOLDER_HITMAN, VERSION.upper())
FOLDER_ALTERNATIVE  = os.path.join("/home/support/heatmap", VERSION.upper())

mapping_inventario = {}

# Funcion para guardar data de diccionarios en un csv
def save_to_csv(data : dict):
    ip = data.get("ip")

    if not ip:
        return

    filename    = os.path.join(FOLDER_OUT_HITMAN, f"{ip}.csv")
    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames = data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


## Funcion para obtener los datos GPS (si no hay, retorna None)
def getVersionData(ip_target : str, time_out : int = 5) -> dict | None:
    global mapping_inventario
    try:
        data_proto_rajant = getRajantData(
            ipv4        = ip_target,
            user        = _ROLES[DEFAULT_ROL],
            passw       = _PASSWORDS[DEFAULT_ROL],
            timeout     = time_out - 2,
            debug_mode  = DEBUG_MODE
        )
        if not data_proto_rajant or not data_proto_rajant.HasField("gps"):
            #print(f"Valores gps vacios en {ip_target}")
            return None

        data_gps = data_proto_rajant.gps.gpsPos
        if not data_gps.ListFields():
            #print(f"Valores gps vacios en {ip_target}")
            return None

        gps_altitud = float(data_gps.gpsAlt)
        my_return_dict = {
            "gpsLat"    : dms_to_dd(data_gps.gpsLat),
            "gpsLong"   : dms_to_dd(data_gps.gpsLong),
            "gpsAlt"    : round(gps_altitud, 2),
        }

        # Datos WIRELESSS
        signal_data = {}
        for wireless in data_proto_rajant.wireless:
            name_interface  = wireless.name
            noise_interface = wireless.noise
            current_metricas = []
            current_min_cost = 4000000

            for peer_data in wireless.peer:
                if not peer_data.enabled:
                    continue
                current_cost = int(peer_data.cost)
                if current_cost < current_min_cost:
                    current_min_cost = current_cost
                    current_metricas = [peer_data.ipv4Address, peer_data.cost, peer_data.rssi, peer_data.signal]

            if current_metricas:
                current_metricas.append(noise_interface)
                signal_data[name_interface] = current_metricas

        # Datos WIRED
        for wired in data_proto_rajant.wired:
            name_interface = wired.name
            if name_interface != "eth0":
                continue
            _cost = -1
            for _peer in wired.peer:
                _cost = _peer.cost
            host_ip     = data_proto_rajant.system.ipv4.gateway
            name_host   = mapping_inventario.get(host_ip, "")
            my_return_dict.update({"eth0" : [host_ip, name_host, _cost]})

        # Datos rptPeer
        for data_rpt_peer in data_proto_rajant.system.rptPeer:
            host_ip     = data_rpt_peer.ipv4Address
            name_host   = mapping_inventario.get(host_ip, "")
            cost        = data_rpt_peer.cost
            my_return_dict.update({"rptPeer" : [host_ip, name_host, cost]})

        if signal_data:
            my_return_dict.update(signal_data)

        if DEBUG_MODE:
            print(f"Diccionario obtenido = {signal_data}\n")

        return my_return_dict

    except Exception as e:
        if DEBUG_MODE:
            print(f"✘ Error en {ip_target} | \"getVersionData()\":\n{e}")
        return None


## Funcion en pararelo para cada equipo obtenido
async def async_task(ip_device, fq_sample) -> dict:
    try:
        dictionary_sistema  = await asyncio.to_thread(getVersionData, ip_device, time_out = fq_sample)
        ping_value          = await asyncio.to_thread(ping_host, ip_device)

        if not dictionary_sistema:
            return

        dictionary_sistema["latencia"]  = ping_value
        dictionary_sistema["ip"]        = ip_device
        dictionary_sistema["fecha"]     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        return dictionary_sistema
    
    except Exception as e:
        if DEBUG_MODE:
            print(f"✘ Error con IP {ip_device} en async_task: {e}")
        return None


## Proceso para manejar tareas asincronicas (en pararelo)
async def process_devices(ip_list : list[str], freq_muestreo : int):
    """Ejecuta todas las inspecciones en paralelo y guarda los resultados."""
    #queue = asyncio.Queue()

    # Ejecutar todas las tareas en paralelo
    tasks = [async_task(ip_device, freq_muestreo) for ip_device in ip_list]
    resultados = await asyncio.gather(*tasks)
    return resultados

##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    if len(sys.argv) < 3:
        print("Uso: python script.py <tiempo_duracion_min> <intervalo_seg>")
        sys.exit(1)

    tiempo_duracion_min     = int(sys.argv[1])
    intervalo_seg           = int(sys.argv[2])

    if intervalo_seg < 5:
        print("Tiempo de muestreo demasiado pequeño, valor MINIMO = 5")
        sys.exit(1)

    ## Obtenemos datos de la lista de equipos tipo LTE de la API
    url_inventario      = DB_API_URL + f"inventario/get"
    filter_inventario   = ["marca", VERSION]

    temp_dict = {
        item["ip"] : item.get("tag") for item in get_request_to_url(url_inventario)
    }
    mapping_inventario.update(temp_dict)

    rajant_list_ip = [
        item["ip"]
        for item in get_request_to_url_with_filters(url_inventario, filter_array = filter_inventario)
        if item.get("anotacion")
        and isinstance(item["anotacion"], str)  # Ensure it's a string before parsing
        and "modo" in (anotacion_dict := json.loads(item["anotacion"]))  # Parse JSON safely
        and anotacion_dict["modo"] == "heatmap"
    ]

    if len(rajant_list_ip) == 0:
        print(f"No hay equipos compatibles con {VERSION} / Hitman")
        raise Exception()

    print(f"Lista de equipos a consultar = {rajant_list_ip}")

    # Crear la carpeta si no existe
    if not os.path.exists(FOLDER_OUT_HITMAN):
        os.makedirs(FOLDER_OUT_HITMAN)
    # Si hay archivos ya scaneados, se eliminaran
    else:
        for file in glob.glob(os.path.join(FOLDER_OUT_HITMAN, "*.csv")):
            os.remove(file)

    total_iterations    = tiempo_duracion_min * 60 // intervalo_seg
    iteration           = 0
    tiempo_finalizacion = time.time() + tiempo_duracion_min * 60

    print(f"Progreso: 0% | Total = {tiempo_duracion_min} min | Intervalo = {intervalo_seg} s")
    current_time        = time.time()
    while current_time < tiempo_finalizacion:
        # Procesamos el escaneo de los datos de los 
        # equipos de manera paralela
        final_results = asyncio.run( process_devices(rajant_list_ip, intervalo_seg) )

        ## Guardamos los datos en un .csv
        for json_data in final_results:
            if json_data:
                save_to_csv(json_data)

        # El equipo esperara a la siguiente marca de tiempo
        elapsed_time    = time.time() - current_time
        sleep_time      = max(0, intervalo_seg - elapsed_time)
        time.sleep(sleep_time)
        current_time    = time.time()

        # Imprimimos el progreso del scaneo
        iteration += 1
        progress = (iteration / total_iterations) * 100
        print(f"Progreso: {progress:.2f}%")


    ## Copiamos y pegamos los resultados obtenidos hacia una carpeta alternativa
    
    # Crear la carpeta si no existe
    if os.path.exists(FOLDER_ALTERNATIVE):
        shutil.rmtree(FOLDER_ALTERNATIVE)

    shutil.copytree(FOLDER_OUT_HITMAN, FOLDER_ALTERNATIVE)

except Exception as e:
    if str(e):
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
        #print(f" > Error Details:\n")
        #print(traceback.format_exc())
