## Smartlink - Captura de datos de Instamesh/Rajant
## Version      : V2025.1
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128
## Tables       : GPS, Rajant, Sensores
import sys
sys.path.append('/usr/smartlink')
from api_sql.fastapi.models.rajant_data_models      import RajantData       as Model
from api_sql.fastapi.models.ubicacion_gps_models    import UbicacionGPS
from api_sql.fastapi.models.sensores_models         import Sensor

from rajant.constants_rajant    import getRajantData, _HCG_RAJANT_PASS, _HCG_RAJANT_USER
from concurrent.futures         import ThreadPoolExecutor
from datetime                   import datetime
from globalHCG                  import *

import traceback
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
DEBUG_MODE      = False
URL_GPS_LIST    = DB_API_URL + "ubicacion_gps/add_list"
URL_SENSOR_LIST = DB_API_URL + "sensores/add_list"
URL_RAJANT_LIST = DB_API_URL + "rajant_data/add_list"

## Funciones personzalidas para Rajant
def convert_mac_hex_to_readable(byte_mac):
    readable_mac = ':'.join(f'{b:02X}' for b in byte_mac)
    return readable_mac


def format_json_rajant(data_proto_rajant):
    rajant_dictionary   = dict()
    gps_dictionary      = dict()
    sensor_dictionary   = dict()
    #_attributes = data_proto_rajant.DESCRIPTOR.fields_by_name

    # Verificamos que el campo deseado se encuentre
    # dentro de la rpta para poder almacenarlo luego
    try:
        # Si hay datos GPS se almacenan
        if data_proto_rajant.HasField("gps"):
            data_gps        = data_proto_rajant.gps.gpsPos
            gps_altura      = float(data_gps.gpsAlt)
            gps_dictionary  = {
                "latitud"   : dms_to_dd(data_gps.gpsLat),
                "longitud"  : dms_to_dd(data_gps.gpsLong),
                "altura"    : round(gps_altura, 2)
            }
            
        # Valores del sistema / sensores
        if data_proto_rajant.HasField("system"):
            sensor_dictionary = {
                "info" : {},
                "valores" : {}
            }
            data_system                 = data_proto_rajant.system
            data_system_sensores        = data_system.sensors
            system_info_dictionary      = sensor_dictionary["info"]
            system_sensores_dictionary  = sensor_dictionary["valores"]

            system_info_dictionary["sysTemperatura"]    = data_system.temperature
            system_info_dictionary["modelo"]            = data_proto_rajant.manufacturer.model
            for _sensor_type in data_system_sensores.DESCRIPTOR.fields_by_name:
                array_data = []
                for data in getattr(data_system_sensores,_sensor_type):
                    array_data.append(data.value.current)
                system_sensores_dictionary[_sensor_type] = array_data

        # Obtenemos los valores de configuracion del equipo
        config_dictionary = dict()
        if True:
            config_dictionary["uptime"]    = data_system.uptime
        rajant_dictionary["config"] = config_dictionary

        # Obtenemos los datos Instamesh
        temp_config_rajant = data_proto_rajant.instamesh
        temp_fields = ["packetsDropped", "packetsMulticast", "packetsReceived", "packetsSent"]
        instamesh_dictionary = dict()
        for _field in temp_fields:
            instamesh_dictionary[_field] = getattr(temp_config_rajant, _field)
        rajant_dictionary["instamesh"] = instamesh_dictionary

        # Obtenemos los valores de Wired
        fields_wired_stats  = ["rxBytes", "txBytes"]
        _cost_wired_list    = []
        final_wired_dictionary = dict()
        # Valores de cada interfaz "wired" que existan
        for _wired_data in data_proto_rajant.wired:
            _wired_dictionary   = dict()
            key_name            = _wired_data.name
            # Valores de Wired
            _stats_data = _wired_data.stats
            for _field in fields_wired_stats:
                _wired_dictionary[_field] = getattr(_stats_data, _field)
            # Valor de Costo
            for _peer_data in _wired_data.peer:
                if _peer_data.HasField("cost"):
                    _cost_wired_list.append(int(_peer_data.cost))
            final_wired_dictionary[key_name] = _wired_dictionary
        if _cost_wired_list:
            final_wired_dictionary["cost"] = min(_cost_wired_list)
        rajant_dictionary["wired"] = final_wired_dictionary
        
        # Obtenemos los valores de Wireless
        fields_wireless         = ["noise", "channel"]
        fields_wireless_stats   = ["rxBytes", "txBytes"]
        _cost_wireless_list     = []

        final_wireless_dictionary = dict()
        for _wireless_data in data_proto_rajant.wireless:
            _wireless_dictionary = dict()
            key_name = _wireless_data.name    
            for _field in fields_wireless:
                _value = getattr(_wireless_data, _field)
                _wireless_dictionary[_field] = _value
            _stats_data = _wireless_data.stats
            for _field in fields_wireless_stats:
                _wireless_dictionary[_field] = getattr(_stats_data, _field)
            for _peer_data in _wireless_data.peer:
                if _peer_data.HasField("cost"):
                    _cost_wired_list.append(int(_peer_data.cost))
            final_wireless_dictionary[key_name] = _wireless_dictionary

        # Obtenemos los valores de rptArp
        fields_rptArp        = ["mac", "action", "cost", "ipv4Address", "encapId"]
        for _rptArp_data in data_proto_rajant.system.rptPeer:
            _rptPeer_dictionary   = dict()
            key_name = "rpt"
            for _field in fields_rptArp:
                _rptPeer_dictionary[_field] = getattr(_rptArp_data, _field)
            final_wireless_dictionary[key_name] = _rptPeer_dictionary

        if _cost_wireless_list:
            final_wireless_dictionary["cost"] = min(_cost_wireless_list)
        rajant_dictionary["wireless"] = final_wireless_dictionary

    except Exception as e:
        print(f"Error al encontrar el valor en el data Rajant:\n{e}")
        print(traceback.format_exc())

    return [rajant_dictionary, gps_dictionary, sensor_dictionary] 


def async_task(ip, queue : queue.Queue):
    data_rajant = getRajantData(ipv4 = ip, user = _HCG_RAJANT_USER, passw = _HCG_RAJANT_PASS,
                                timeout = 5, debug_mode = DEBUG_MODE)
    if data_rajant is None:
        return
    #print(data_rajant)
    current_date        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    list_dict_output    = format_json_rajant(data_rajant)
    for _dict in list_dict_output:
        if _dict:
            _dict["ip"]       = ip
            _dict['fecha']    = current_date
    
    queue.put(list_dict_output)


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos RAJANT de la API
    url_inventario      = DB_API_URL + f"inventario/get"
    filter_inventario   = ["marca", MARCA]
    subscribers         = [ item["ip"] for item in get_request_to_url_with_filters(url_inventario, filtrer_array = filter_inventario) ]
    print(f"Se han detectado un total de {len(subscribers)} equipos en Inventario")

    q = queue.Queue()
    max_threads_number = 25

    list_groups_ip_to_request = group_ips(subscribers, max_group_size = max_threads_number)
    once_model      = True
    once_sensores   = True
    with ThreadPoolExecutor(max_threads_number) as executor:
        for _group in list_groups_ip_to_request:
            futures = [executor.submit(async_task, _ip, q) for _ip in _group]
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()
            # Procesar los resultados inmediatamente
            model_array_list, sensores_array_list, gps_array_list = [], [], []

            while not q.empty():
                _rajant, _gps, _sensores   = q.get()
                # Obtenemos el diccionario para subir los datos Rajant:
                if _rajant:
                    model_array_list.append(Model(**_rajant))
                if _gps:
                    gps_array_list.append(UbicacionGPS(**_gps))
                if _sensores:
                    sensores_array_list.append(Sensor(**_sensores))

            if model_array_list:
                if once_model:
                    once_model = False
                    restart_log_file(log_file, Model)
                post_request_to_url_model_array(URL_RAJANT_LIST, array_model_to_post = model_array_list,
                                                _debug = DEBUG_MODE)
                write_log_files(log_file, model_array_list)

            if gps_array_list:
                post_request_to_url_model_array(URL_GPS_LIST, array_model_to_post = gps_array_list, 
                                                _debug = DEBUG_MODE)
            
            if sensores_array_list:
                if once_sensores:
                    once_sensores = False
                    restart_log_file(log_sensores, Sensor)
                post_request_to_url_model_array(URL_SENSOR_LIST, array_model_to_post = sensores_array_list,
                                                _debug = DEBUG_MODE)
                write_log_files(log_sensores, sensores_array_list)

except Exception as e:
    if str(e):
        print(f" !! {script_folder} main function error: {e}")
        #print(" > Error Details:")
        #print(traceback.format_exc())











