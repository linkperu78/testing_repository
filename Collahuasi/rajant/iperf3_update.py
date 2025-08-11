from smartlink.global_utils import FOLDER_OUTPUT
from smartlink.models.rajant_performance_models import rajant_performance
from smartlink.http_utils   import DB_API_URL, get_request_to_url_with_filters, post_request_to_url_model_array
from bcapi_utils            import iperf3_broker

import pandas as pd
import traceback
import argparse
import json
import csv
import os

## Local folder data
script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)
output_file     = os.path.join(FOLDER_OUTPUT, "iperf3_result.csv")

# Definición de argumentos
_DEBUG_MODE = False
parser = argparse.ArgumentParser(description="Script IPERF3 test performance with MariaDB")
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
parser.add_argument('-t', '--time-scan', type=int, default=15, help='Scan interval time [s] in seconds')
parser.add_argument('-b', '--bias', type=float, default=1.0, help='El valor minimo [Mbps] para ser considerado exitoso')

# Lectura de argumentos
args = parser.parse_args()
_DEBUG_MODE     = args.debug
BASE_TIME_SCAN  = args.time_scan
BIAS_MIN_BANDWIDTH  = args.bias

# Variables Globales
INVENTORY_URL   = DB_API_URL + "inventario/get"
KEYNAME_SERVER  = "server_bcapi"
ROLE_RAJANT     = "co"
URL_POST_DATA   = DB_API_URL + "iperf3/add_list"
CSV_COL_NAMES   = ["cliente", "servidor", "latencia", "send_Mbps", "send_coreU", "rec_Mbps", "rec_coreU", "fecha"]
FIELD_INDEX = {
    "ip": 0,         # cliente
    "server": 1,     # servidor
    "latencia": 2,   # latencia
    "tx_bw": 3,      # send_Mbps
    "tx_core": 4,    # send_coreU
    "rx_bw": 5,      # rec_Mbps
    "rx_core": 6,    # rec_coreU
    "fecha": 7       # fecha
}

def get_result_iperf3(_client, _server, _role_rajant = "co", _timeout = 5, scantime = 10, _debug = _DEBUG_MODE) -> list:
    _client_broker = iperf3_broker(
        ip_cliente  = _client,
        role        = _role_rajant,
        timeout     = _timeout,
        debug_mode  = _debug
    )
    
    resultado_temp  = _client_broker.start_test_iperf3(
        ip_server_target = _server,
        duration_time    = scantime
    )

    return resultado_temp

def convert_array_to_model(input_data_array: list) -> rajant_performance:
    data_array = [-1 if _value == "-" else _value for _value in input_data_array]
    return rajant_performance(
        ip=data_array[FIELD_INDEX["ip"]],
        fecha=data_array[FIELD_INDEX["fecha"]],
        server=data_array[FIELD_INDEX["server"]],
        latencia=data_array[FIELD_INDEX["latencia"]],
        bandwidth={
            "Tx": data_array[FIELD_INDEX["tx_bw"]],
            "Rx": data_array[FIELD_INDEX["rx_bw"]],
        },
        coreU={
            "Tx": data_array[FIELD_INDEX["tx_core"]],
            "Rx": data_array[FIELD_INDEX["rx_core"]],
        }
    )


""" - - - - - - - - - - -  PROGRAMA PRINCIPAL  - - - - - - - - - - - """
if __name__ == "__main__":
    # Leemos el archivo para obtener la lista de ip para clientes y servidores
    total_data      = []
    not_connected   = []
    observed_ip     = []
    
    clients_list    = []
    try:
        ## -----------------------------------------------------------------------------------
        # Obtenemos de los equipos marcados para IPERF3 usando la API Smartlink
        inventario = get_request_to_url_with_filters(INVENTORY_URL, filter_array = ["marca", "Rajant"])
        if not inventario:
            raise Exception(f"Inventario vacio con URL = {INVENTORY_URL}")
        
        for row_client in inventario:
            _ip_target      = row_client["ip"]
            _client_config  = []
            anotacion_value = row_client.get("anotacion")
            if anotacion_value:
                try:
                    _data = json.loads(anotacion_value)
                    _server_target = _data.get(KEYNAME_SERVER)
                    if _server_target:
                        _client_config = [_ip_target, _server_target]
                except json.JSONDecodeError:
                    continue

            if _client_config:
                clients_list.append(_client_config)
            else:
                if _DEBUG_MODE:
                    print(f"El equipo {_ip_target} no posee '{KEYNAME_SERVER}' en la COLUMNA 'anotación'")

        if _DEBUG_MODE:
            print(clients_list)
        
        ## -----------------------------------------------------------------------------------
        ## Con el inventario de equipos Rajant para realizar Performance, realizamos el IPERF3
        print(f"\n 1st Eval: Evaluando el 'valor' del bandwidth en equipos Rajant")

        for _client, _server in clients_list:
            print(f"\n... Evaluando cliente: {_client}")
            
            resultado_temp  = get_result_iperf3(
                _client     = _client,
                _server     = _server,
                _role       = ROLE_RAJANT,
                _timeout    = 5,
                _scantime   = BASE_TIME_SCAN,
                _debug      = _DEBUG_MODE
            )
            
            _evaluacion = resultado_temp[3]
            total_data.append(resultado_temp)

            if _evaluacion == "-":
                if _DEBUG_MODE:
                    print(f"• 1era Ev : {_client} --> Empty")
                not_connected.append([_client, _server])
                continue

            if _evaluacion < BIAS_MIN_BANDWIDTH:
                if _DEBUG_MODE:
                    print(f"• 1era Ev : {_client} --> Not Acceptable")
                observed_ip.append([_client, _server])

        if _DEBUG_MODE:
            print(f" \tObservados : {len(observed_ip)}\n \tVacios : {len(not_connected)}\n")

        # Creamos un archivo 'dataframe' para almacenar los valores obtenidos
        df_iperf3_result    = pd.DataFrame(total_data, columns = CSV_COL_NAMES)

        # Para los equipos con un valor obtenido menor al aceptable, se les realiza una nueva evaluacion
        if observed_ip:
            print(f"\n Re-eval: Reevaluando {len(observed_ip)} equipos con bajos o nulos resultados")
            
        for _client, _server in observed_ip:
            if _DEBUG_MODE:
                print(f"... Reevaluando Cliente: {_client} / Server: {_server}")

            resultado_temp  = get_result_iperf3(
                _client     = _client,
                _server     = _server,
                _role       = ROLE_RAJANT,
                _timeout    = 5,
                _scantime   = BASE_TIME_SCAN,
                _debug      = _DEBUG_MODE
            )
            _evaluacion = resultado_temp[2]
            
            if _evaluacion == "-":
                if _DEBUG_MODE:
                    print(f"Re-eval: {_client} / {_server} Empty")
                continue
            
            # Obtenemos los valores donde hayan coindicencia del valor ip de _client y _server
            mask = (df_iperf3_result['cliente'] == _client) & (df_iperf3_result['servidor'] == _server)
            df_iperf3_result.loc[mask] = resultado_temp


        # Finalmente guardamos los datos obtenidos antes de la segunda ronda
        df_iperf3_result.to_csv(output_file, index = False)

        ## - - - - - - - - EVALUACION DE RESULTADOS VACIOS - - - - - - 
        for a in range(2, 4): # [2, 3]
            if not_connected:
                print(f"\n ○ ○ {a}° Eval: Reevaluando el 'valor' del bandwidth de {len(not_connected)} equipos Rajant")
            
            still_not_connected = []
            
            for _client, _server in not_connected:
                resultado_temp  = get_result_iperf3(_client, 
                                                    _server,
                                                    _role       = ROLE_RAJANT,
                                                    _timeout    = 5, 
                                                    scantime    = BASE_TIME_SCAN,
                                                    _debug      = _DEBUG_MODE)
                _evaluacion = resultado_temp[2]
                if _evaluacion == "-":
                    still_not_connected.append([_client, _server])
                    continue

                mask = (df_iperf3_result['cliente'] == _client) & (df_iperf3_result['servidor'] == _server)
                df_iperf3_result.loc[mask] = resultado_temp

            not_connected = still_not_connected.copy()

        if _DEBUG_MODE:
            print("\n Valores finales obtenidos")
            for _, row in df_iperf3_result.iterrows():
                print(f" \t- - - - - - -\n{row}")
        
        ## Sobreescribimos el archivo con los datos finales
        df_iperf3_result.to_csv(output_file, index = False)

        ## Preparamos los datos obtenidos en una lista de Model para añadirlos en la base de datos
        list_models_to_storage = [
            convert_array_to_model(row.tolist())
            for _, row in df_iperf3_result.iterrows()
        ]

        ## Enviamos los datos a la base de datos mediante el uso de Smartlink API
        post_request_to_url_model_array(
            url = URL_POST_DATA,
            timeout = 5,
            array_model_to_post = list_models_to_storage,
            _debug = _DEBUG_MODE
        )

        print(f"FINALIZADO")

    except Exception as e:
        print(f"Error en iperf3_mariadb.py =\n{e}")
        if _DEBUG_MODE:
            print(traceback.format_exc())
