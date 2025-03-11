FOLDER_OUTPUT       = "/usr/smartlink/outputs"
_BCUTILS_AUTH_DB    = '/usr/smartlink/authdb.json'
TIMEOUT_API_REQUEST = 5
TIMEOUT_SNMP_QUERY  = 5
USER_SSH_MIKROTIK   = "admin"
PASS_SSH_MIKROTIK   = "HCG"

import requests
import subprocess
import csv
import psutil
import socket

def get_ipv4_address(interfaces=("ens192", "eth0")):
    for interface in interfaces:
        addrs = psutil.net_if_addrs().get(interface, [])
        for addr in addrs:
            if addr.family == socket.AF_INET:  # IPv4 address
                return addr.address
    return None  # Return None if no valid IP is found

# Get IPv4 address dynamically
ip_address = get_ipv4_address()
if ip_address:
    DB_API_URL = f"http://{ip_address}:8000/"
else:
    DB_API_URL = f"http://localhost:8000/"      # Set the correct server static IP


## Funcion para agrupar IP's para tareas en paralelo
def group_ips(ip_list, max_group_size = 25):
    # Create a list of sublists with up to max_group_size IPs in each
    grouped_ips = [ip_list[i:i + max_group_size] for i in range(0, len(ip_list), max_group_size)]
    return grouped_ips


## Funcion para realizar consultas a una URL con timeout de 5 segundos
def get_request_to_url(url: str, timeout : int = 5, column_filter : str = None, optional_param : dict = None) -> list:
    try:
        optional_param = optional_param or {}  # Avoid mutable default argument
        response = requests.get(url, params = optional_param, timeout=timeout)
        #print("GET URL:", response.url)
        response.raise_for_status()  # Lanza una excepción si el código de estado es 4xx o 5xx
        
        inventario_data = response.json()
        if not isinstance(inventario_data, list):
            #logging.error(f"Respuesta inesperada de {url}, se esperaba una lista.")
            return []

        # Si no se especifica column_filter, devolver todos los datos
        if not column_filter:
            return inventario_data

        # Filtrar solo los valores que contienen la clave
        result_list = [record[column_filter] for record in inventario_data if column_filter in record]

        return result_list

    except requests.exceptions.RequestException as e:
        print(f"Error al consultar {url} /\n Error = {e}")
        return []


## Funcion para realizar consultas a una URL con timeout de 5 segundos usando filtros
def get_request_to_url_with_filters(url: str, timeout : int = 5, filtrer_array : list = []) -> list:
    if len(filtrer_array) != 2:
        return []
    
    for _value in filtrer_array:
        if _value == "":
            return []

    try:
        column_filter, value_filter = filtrer_array
        full_url = url + f"/{column_filter}/{value_filter}"
        #print(f"URL API = {full_url}")
        response = requests.get(full_url, timeout=timeout)
        #print("GET URL:", response.url)
        response.raise_for_status()  # Lanza una excepción si el código de estado es 4xx o 5xx
        
        inventario_data = response.json()
        if not isinstance(inventario_data, list):
            #logging.error(f"Respuesta inesperada de {url}, se esperaba una lista.")
            return []

        # Filtrar solo los valores que contienen la clave
        result_list = [record for record in inventario_data]

        return result_list

    except requests.exceptions.RequestException as e:
        print(f"Error al consultar {full_url}\n Error = {e}")
        return []


## Funcion para realizar POST request a la API
def post_request_to_url_model_array(url: str, timeout : int = 5, array_model_to_post : list = []) -> None:
    if not array_model_to_post:
        return
    
    try:
        response = requests.post(
            url, 
            json = [obj.model_dump() for obj in array_model_to_post], 
            timeout = timeout
        )
        #print("POST URL:", response.url)
        response.raise_for_status()  # Automatically raises an exception for 4xx/5xx errors
        print(f"- ✔ Successfully added {len(array_model_to_post)} records to the database.")
    
    except requests.RequestException as e:
        print(f"- ✘ Error sending data to {url}:\n{e}")


## Function for Printing the Log File 
def write_log_files(file_name : str, array_models_with_data : list = []):
    if not array_models_with_data:  # Prevent empty writes
        return
    
    # Generar un log de este script en outputs
    with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
        fieldnames = array_models_with_data[0].model_dump().keys()
        ordered_fieldnames = ['ip', 'fecha'] + [key for key in fieldnames if key not in ['ip', 'fecha']]
        writer = csv.DictWriter(csv_file, fieldnames = ordered_fieldnames)
        # Escribir encabezado
        #writer.writeheader()
        # Convertir objetos Pydantic a diccionarios y escribir filas
        writer.writerows([obj.model_dump() for obj in array_models_with_data])


## Vacia el archivo log y coloca las columnas nombres
def restart_log_file(file_name : str , model):
    # Overwrite the file initially with column names only
    with open(file_name, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = model.model_fields.keys()
        ordered_fieldnames = ['ip', 'fecha'] + [key for key in fieldnames if key not in ['ip', 'fecha']]
        writer = csv.DictWriter(csv_file, fieldnames=ordered_fieldnames)
        writer.writeheader()  # Write only the column names



## Funcion para consultar SNMP
def snmp_request(oid, ip_host, credentials : dict = {}, _timeout = TIMEOUT_SNMP_QUERY):
    values = {}

    command_snmp    = ['snmpwalk']
    _version        = "2c" if credentials.get("version", 2) == 2 else str(credentials.get("version", 2))
    command_snmp    += ["-v", _version]

    if credentials.get("version", 2) > 2:
        command_snmp += [
            "-l", credentials.get("mode", "noAuthNoPriv"),
            "-u", credentials.get("user", "no_user"),
            "-a", credentials.get("auth_mode", "MD5"),
            "-A", credentials.get("auth_pass", "no_AUTH_pass"),
            "-x", credentials.get("priv_mode", "AES"),
            "-X", credentials.get("priv_pass", "no_PRIV_pass")
        ]
    else:   
        command_snmp += ["-c", credentials.get("community", "public")]
    
    command_snmp += ["-O", "nq", "-t", str(_timeout), ip_host, oid]

    try:
        result = subprocess.run(command_snmp, capture_output=True, text=True, check=True, timeout = _timeout + 2).stdout
        #print(f"->> {result}")

    except subprocess.CalledProcessError as e:
        print(f"SNMP error: {e.stderr}")
        return -1
    
    except subprocess.TimeoutExpired:
        print("SNMP request timed out")
        return -1
    
    if "No Such " in result:
        return None

    lines = result.strip().split("\n")
    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) == 2:
            oid_str, value = parts
            index = oid_str.split(".")[-1]  # Extract last part of OID as index
            values[index] = value.strip().strip('"')
    
    if len(values) == 1:
        return next(iter(values.values()))
    
    return values


if __name__ == "__main__":
    print(f"IP obtenida = {ip_address} | {DB_API_URL}")