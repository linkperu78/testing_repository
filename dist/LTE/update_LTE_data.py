# =============================================================================
#                   Smartlink - Captura de datos de Cambium
# =============================================================================
#  Versión       : V2025.4
#  Autor         : HCG-GROUP, Área de Backend
#  Contacto      : Anexo 3128
#  Tablas        : LTE_data, ubicacion_gps
# =============================================================================
from smartlink.models.LTE_data_models       import LTE as Model
from smartlink.models.ubicacion_gps_models  import UbicacionGPS
from smartlink.error_utils  import KEYNAME_ERROR_DICT, multiple_storage_errors
from smartlink.ssh_utils    import mySSHClient
from smartlink.snmp_utils   import mySNMPClient
from smartlink.global_utils import FOLDER_OUTPUT, group_ips
from smartlink.csv_utils    import write_log_files, restart_log_file
from smartlink.http_utils   import DB_API_URL, get_request_to_url, get_request_to_url_with_filters, post_request_to_url_model_array
from smartlink.json_utils   import load_json_to_dict
from LTE_module             import USER_SSH_MIKROTIK, PASS_SSH_MIKROTIK, SSH_COMMAND_LIST, parse_LTE_Mikrotik_dictionary
from concurrent.futures     import ThreadPoolExecutor
from datetime               import datetime
import argparse
import queue
import os

script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)
oid_folder      = os.path.join(script_folder, "snmp_json")

TIPO                = "LTE"
MAX_CONCURRENTS     = 25
DB_INVENTARIO_URL   = DB_API_URL + "inventario/get"
DB_SNMP_CONF_URL    = DB_API_URL + "snmp_conf/get_list_id/"
URL_MODEL_LIST      = DB_API_URL + f"{TIPO}_data/add_list"
URL_GPS_LIST        = DB_API_URL + "ubicacion_gps/add_list"

## Direccion de archivos de salida en /usr/smartlink/outputs
log_file        = os.path.join(FOLDER_OUTPUT, f"{TIPO}_data.csv")

## Activacion del modo DEBUG
_DEBUG_MODE = False
parser = argparse.ArgumentParser(description="Script para capturar datos LTE por SSH y SNMP")
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
parser.add_argument('-t', '--test', action='store_true', help='Enable test environment')
args = parser.parse_args()
_DEBUG_MODE = args.debug

## Carga de los diccionarios para mapear OID's
base_dict_snmp = load_json_to_dict( os.path.join(oid_folder, "mikrotik2024.json") )
global_error_array = []

## Funciones personzalidas
def async_task(ip_device, conf_snmp, queue : queue.Queue):
    hora_de_consulta        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # - - - - - Obtenemos los datos SSH
    ssh_agent = mySSHClient(ip_target       = ip_device, 
                            user_ssh        = USER_SSH_MIKROTIK, 
                            password_ssh    = PASS_SSH_MIKROTIK,
                            debug_mode      = _DEBUG_MODE, 
                            timeout         = 10)
    
    data_ssh_dict = ssh_agent.mapping_command_ssh(SSH_COMMAND_LIST, 3, False)
    error_ssh = data_ssh_dict.pop(KEYNAME_ERROR_DICT, None)
    if error_ssh:
        error_ssh = [ip_device, hora_de_consulta, error_ssh]
        queue.put( [{}, {}, error_ssh] )
    data_ssh = parse_LTE_Mikrotik_dictionary(data_ssh_dict)


    # - - - - - Obtenemos los datos SNMP
    snmp_agent = mySNMPClient(ip_target     = ip_device, 
                              timeout       = 5, 
                              debug_mode    = False)
    snmp_agent.update_credentials(conf_snmp)
    data_snmp   = snmp_agent.mapping_OID_dict(base_dict_snmp, list)
    error_snmp  = data_snmp.pop(KEYNAME_ERROR_DICT, None)
    if error_snmp:
        error_snmp = [ip_device, hora_de_consulta, error_snmp]
        queue.put( [{}, {}, error_snmp] )

    if not data_ssh and not data_snmp:
        if _DEBUG_MODE:
            print(f"{ip_device} Failed: No data obtained")
        return

    # - - -  Sistema   - - - 
    field_sistema = ['name', 'type', 'APN', 'manufacturer', 'model', 'IMEI', 'IMSI']
    dictionary_sistema = {k: data_ssh[k] for k in field_sistema if k in data_ssh} if data_ssh else {}
            
    # - - -   Enlace   - - -  
    list_dictionary_enlaces = None
    if data_snmp:
        key_list = [k for k, v in data_snmp.items() if isinstance(v, list)]
        if key_list:
            num_items = len(data_snmp[key_list[0]])
            list_dictionary_enlaces = [
                {k: data_snmp[k][i] for k in key_list}
                for i in range(num_items)
            ]

    # - - -   Estado   - - -  
    field_estado = ['status', 'network-mode', 'rssi', 'rsrq', 'rsrp', 'current-operator', 'lac', 'current-cellid', 'enb-id', 'sector-id']
    dictionary_estado = {k: data_ssh[k] for k in field_estado if k in data_ssh} if data_ssh else {}
    model_dictionary = {
        "ip"        : ip_device,
        "fecha"     : hora_de_consulta,
        "sistema"   : dictionary_sistema,
        "enlaces"   : list_dictionary_enlaces,
        "estado"    : dictionary_estado 
    }

    list_gps_keys = ["latitud", "longitud", "altura"]
    if data_ssh and all(k in data_ssh for k in ["latitud", "longitud"]):
        dictionary_gps = {k: data_ssh[k] for k in list_gps_keys if k in data_ssh}
    else:
        dictionary_gps = None

    queue.put( [model_dictionary, dictionary_gps, {}] )


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos tipo LTE de la API
    filter_database = ["tipo", TIPO]
    raw_inventory   = get_request_to_url_with_filters(DB_INVENTARIO_URL, filter_array = filter_database)
    subscribers     = [ [row["ip"], row["snmp_conf"]] for row in raw_inventory]

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
    subscribers         = [ [_ip, config_dict.get(_index, {})] for _ip, _index in subscribers]

    if _DEBUG_MODE: 
        for suscriptor in subscribers: print(suscriptor)

    q = queue.Queue()    
    list_groups_ip_to_request = group_ips(subscribers, max_group_size = MAX_CONCURRENTS)
    once = True

    with ThreadPoolExecutor(MAX_CONCURRENTS) as executor:
        for _group in list_groups_ip_to_request:
            futures = [executor.submit(async_task, _ip, _conf_snmp, q) for _ip, _conf_snmp in _group]
            
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()

            # Procesar los resultados inmediatamente
            model_array_list, gps_array_list = [], []
            while not q.empty():
                model_data, gps_data, error_message = q.get()
                if model_data:
                    model_array_list.append(Model(**model_data))
                if gps_data:
                    gps_array_list.append(UbicacionGPS(**gps_data))
                if error_message:
                    global_error_array.append(error_message)

            if model_array_list:
                if once:
                    restart_log_file(log_file, Model)
                    once = False
                post_request_to_url_model_array(URL_MODEL_LIST, array_model_to_post = model_array_list)
                write_log_files(log_file, model_array_list)

            if gps_array_list:
                post_request_to_url_model_array(URL_GPS_LIST, array_model_to_post = gps_array_list)

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
            print(f"Error al guardar los fallos en {TIPO} : {e}")

except Exception as e:
    if str(e):
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
        if _DEBUG_MODE:
            import traceback
            print(f" > Error Details:\n")
            print(traceback.format_exc())





    