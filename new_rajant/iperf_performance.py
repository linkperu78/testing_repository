''' LIBRARIES '''
from bcapihcg.Common_pb2 import Iperf3Result
import bcapihcg.Common_pb2
import bcapihcg.Message_pb2
from bcutilshcg import bcsession
from time import sleep
from datetime import datetime as dt

import pandas as pd
import os

## Local folder data
script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

## Valores Constantes
SERVICE_V11         = 'com.rajant.breadcrumb.v11'
SERVICE_V10         = 'com.rajant.breadcrumb.v10'
_BCUTILS_AUTH_DB    = '/usr/smartlink/authdb.json'
#VALOR_MIN_BANDWIDTH = 10.0
FOLDER_OUTPUT       = "/usr/smartlink/outputs"
VALOR_MIN_BANDWIDTH = 1.0
BASE_TIME_SCAN      = 15
OFFSET_TIME_SCAN    = 10
TIME_WAIT           = 20

# Columnas para el DataFrame
df_iperf3_col_names = ["cliente", "servidor", "latencia", "send_Mbps", "send_coreU", "rec_Mbps", "rec_coreU", "fecha"]
NUMBER_OF_COL = len(df_iperf3_col_names)

# Direccion de los archivos
file_reference_name = "lista_equipos_rajant.txt"
file_path           = os.path.join(script_folder, file_reference_name)
file_results_name   = "iperf3_result.csv"
output_file         = os.path.join(FOLDER_OUTPUT, file_results_name)


def get_session(ip_rajant, my_port = 2300, my_role = bcsession.SESSION_ROLE_CO, my_passphrase = "BVC-Co-25&", timeout = 1.0):
    try:
        _session = bcsession.BcSession()
        _session.start(
            ip_rajant,
            port = my_port,
            role = my_role,
            passphrase = my_passphrase,
            timeout = timeout,
        )
        return _session

    except Exception:
        print("Unable to start BreadCrumb session")
        return None


def get_request_format_iperf3(id_server : str, time_duration : int):
    try:
        rajant_request          = bcapihcg.Message_pb2.BCMessage()
        task_formatted          = bcapihcg.Common_pb2.TaskCommand()
        task_formatted.action   = bcapihcg.Common_pb2.TaskCommand.TaskAction.IPERF3

        # Configurar el campo iperf3 dentro del TaskCommand
        iperf3_command          = task_formatted.iperf3
        iperf3_command.server   = id_server     # ID servidor del servidor
        iperf3_command.testMode = bcapihcg.Common_pb2.TaskCommand.Iperf3.TestMode.TCP  # Tipo de comunicación TCP

        if time_duration > 60:
            #print(f"Warning! Para solicitud iperf3 rajant : Tiempo maximo permitido = 60 seg")
            time_duration = 60

        iperf3_command.time     = time_duration  # Duración de la prueba en segundos
        iperf3_command.reverse  = False  # No realizar tráfico inverso

        # Colocamos los campos estructurados en el request
        rajant_request.runTask.CopyFrom(task_formatted)

        return rajant_request

    except Exception as e:
        print(f" ↓ Error en get_request_format_iperf3():\n'{e}'\n")
        return None


def iperf3_scan(ip_client : str, ip_server : str, duration : int):
    # Creamos la session para el cliente
    data_result_iperf3 = ["-"] * NUMBER_OF_COL
    data_result_iperf3[0] = ip_client
    data_result_iperf3[1] = ip_server
    data_result_iperf3[-1] = dt.now().replace(microsecond = 0)

    try:
        rajant_session  = get_session(ip_client, timeout = 2)
        if not rajant_session:
            raise Exception(f"No se pudo establecer conexion con {ip_client}")
        #print(f"- - - Creando cliente = {ip_client} / Resultado = {rajant_session}")

        # Funcion para obtener el mensaje formateado para Iperf3
        rajant_request  = get_request_format_iperf3(ip_server, duration)

        # Solicitar al equipo realizar un query de Iperf3
        rajant_session.sendmsg(rajant_request)
        resp_request    = rajant_session.recvmsg()

        # Deestructuramos el mensaje de respuesta para obtener
        result_query    = resp_request.runTaskResult
        query_result    = result_query.status
        query_id        = result_query.id

        if query_result != bcapihcg.Message_pb2.BCMessage.Result.SUCCESS:
            rajant_session.stop()
            raise Exception(f"Peticion Rajant / IPERF3\n- IPv4 Cliente = '{ip_client}'\n- IPv4 Servidor = '{ip_server}' ")

        time_duration   = duration

        if time_duration > 60:
            time_duration = 60

        total_waiting_time = int(time_duration + OFFSET_TIME_SCAN)
        sleep(total_waiting_time)

        #print(f"\n- - - - - - - - -\nResultado del Iperf3:")
        fecha_resultado = dt.now().replace(microsecond = 0)
        fecha_resultado = f"{fecha_resultado}"

        ## Nos preparamos para procesar el resultado del Iperf3
        result_iperf3_serial    = bcapihcg.Common_pb2.Iperf3Result()    # Formato para de la respuesta
        server_query_result     = bcapihcg.Message_pb2.BCMessage()

        ## Colocamos los parametros y la estructura para la consulta del resultado
        task_output_request     = bcapihcg.Common_pb2.TaskOutputRequest()
        task_output_request.id  = query_id
        server_query_result.taskOutputRequest.CopyFrom(task_output_request)

        # Enviar el mensaje y procesar la respuesta
        rajant_session.sendmsg(server_query_result)
        response_iperf3_result  = rajant_session.recvmsg()
        response_result_status  = response_iperf3_result.taskOutputResponse.status

        if response_result_status != bcapihcg.Message_pb2.BCMessage.Result.SUCCESS:
            rajant_session.stop()
            raise Exception("Error en recibir resultado del IPERF3 | Rajant")

        data_result     = response_iperf3_result.taskOutputResponse.data
        rajant_session.stop()

        result_iperf3_serial.ParseFromString(data_result)

        ## Extraemos los datos deseados para almacenarlos en un array de salida
        result_ip_cliente   = result_iperf3_serial.sender
        result_ip_server    = result_iperf3_serial.receiver
        result_latency      = result_iperf3_serial.latency
        result_send_bps     = result_iperf3_serial.sendresults.bps
        result_send_coreU   = result_iperf3_serial.sendresults.coreUtilization
        result_rec_bps      = result_iperf3_serial.receiveresults.bps
        result_rec_coreU    = result_iperf3_serial.receiveresults.coreUtilization

        result_latency      = round(result_latency, 3)
        result_send_bps     = round(result_send_bps / 1_000_000, 3)
        result_rec_bps      = round(result_rec_bps / 1_000_000, 3)

        data_result_iperf3  = [result_ip_cliente, result_ip_server, result_latency,
                               result_send_bps, result_send_coreU,
                               result_rec_bps, result_rec_coreU,
                               fecha_resultado]

        sleep(TIME_WAIT - OFFSET_TIME_SCAN)

    except Exception as e:
        print(f"\n ♠ Error server = {ip_server} con cliente = {ip_client}:\n{e} ")

    finally:
        #print("Sesión finalizada.")
        return data_result_iperf3


# Leer el archivo de texto y procesar las listas de servidores y clientes
def load_ip_lists(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    list_ip_servers = []
    list_ip_clients = []
    current_section = None

    # Procesar cada línea del archivo
    for line in lines:
        line = line.strip()  # Eliminar espacios en blanco y saltos de línea
        if not line or line.startswith("#"):  # Ignorar líneas vacías o comentarios
            continue

        if line == "[Servidores]":
            current_section = "servers"
        elif line == "[Clientes]":
            current_section = "clients"
        else:
            if current_section == "servers":
                list_ip_servers.append(line)
            elif current_section == "clients":
                list_ip_clients.append(line)

    return list_ip_servers, list_ip_clients


""" - - - - - - - - - - -  PROGRAMA PRINCIPAL  - - - - - - - - - - - """
if __name__ == "__main__":

    # Leemos el archivo para obtener la lista de ip para clientes y servidores
    list_ip_servers, list_ip_clients = load_ip_lists(file_path)

    total_data  = []
    observed_ip = []
    # Realizamos el scaneo hacia cada servidor mediante cada cliente
    for _server in list_ip_servers:
        print(f"\nServidor = {_server}")

        for _client in list_ip_clients:
            if _client == _server:
                continue

            print(f" \t - Evaluando cliente: {_client} . . .")

            resultado_temp  = iperf3_scan(_client, _server, BASE_TIME_SCAN)

            _evaluacion     = resultado_temp[3]

            if _evaluacion != "-":
                if _evaluacion < VALOR_MIN_BANDWIDTH:
                    observed_ip.append([_client, _server])

            total_data.append(resultado_temp)

    #print(total_data)
    df_iperf3_result = pd.DataFrame(total_data, columns=df_iperf3_col_names)

    for _client, _server in observed_ip:
        resultado_temp  = iperf3_scan(_client, _server, BASE_TIME_SCAN)
        _evaluacion       = resultado_temp[2]

        if _evaluacion == "-":
            continue

        # Obtenemos los valores donde hayan coindicencia del valor ip de _client y _server
        mask = (df_iperf3_result['cliente'] == _client) & (df_iperf3_result['servidor'] == _server)
        df_iperf3_result.loc[mask] = resultado_temp


    df_iperf3_result.to_csv(output_file, index = False)
