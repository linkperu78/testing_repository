import re
import paramiko
import subprocess
import json

USER_SSH_MIKROTIK = "admin"
PASS_SSH_MIKROTIK = "HCG"

SSH_COMMAND_LIST = [
    '/interface/lte/monitor lte1 once',
    '/interface print detail',
    '/interface/lte/ print detail',
    '/interface/lte/at-chat [find] input="AT\$GPSACP"'
]

# Funcion para deestructurar el output del commando: "/interface/lte/monitor lte1 once"
def parse_interface_lte_monitor_once(message: str) -> dict:
    #print(f"\nparse_interface_lte_monitor_once\n{message}")
    parse_dict = {}
    for line in message.strip().split("\n"):
        if ":" not in line:
            continue  # Skip invalid lines
        key, value = line.split(":", 1)
        key = key.strip().replace(" ", "_")  # Convert to a valid key
        value = value.strip()
        # Convert numbers where possible
        if value and value.replace("-", "").isdigit():
            value = int(value)  # Convert to integer
        elif value and value.replace(".", "", 1).replace("-", "", 1).isdigit():
            value = float(value)  # Convert to float
        parse_dict[key] = value
    return parse_dict


# Funcion para deestructurar el output del commando: "/interface print detail"
def parse_interface_detail(message: str) -> dict:
    # Initialize the result dictionary
    lte_dict    = {}
    lines       = message.splitlines()
    
    # Initialize variables for holding interface data and the current interface's data
    interfaces = []
    current_interface = []
    for line in lines:
        if line.strip():  # Skip empty lines
            if line.strip()[0].isdigit():  # Line starting with a digit indicates a new interface
                if current_interface:  # Save the current interface data before starting a new one
                    interfaces.append("\n".join(current_interface))
                current_interface = [line]  # Start a new interface section
            else:
                current_interface.append(line)
    if current_interface:
        interfaces.append("\n".join(current_interface))

    message = ""
    for row in interfaces:
        if 'type="lte"' in row:
            message = row

    key_value_pairs = re.findall(r'(\S+?)="([^"]+)"', message)  # For quoted values
    non_quoted_pairs = re.findall(r'(\S+?)=([^\s]+)', message)  # For non-quoted values


    # Populate the dictionary with both quoted and non-quoted key-value pairs
    for key, value in key_value_pairs + non_quoted_pairs:
        # Remove quotes from the key if present
        key = key.replace('"', '')
        # Clean up the key and value (remove leading/trailing whitespaces if any)
        lte_dict[key] = value.strip()

    return lte_dict


def procesar_salida(output):
    vm_dict_info    = {}

    # Dividimos la salida por cada comando
    comandos        = [seccion.strip() for seccion in output.split("•") if seccion.strip()]

    for _i, comando in enumerate(comandos, 1):
        if _i == 1:
            # pin-status / registration-status / functionality / manufacturer / model
            current_dict    = parse_interface_lte_monitor_once(comando)
            vm_dict_info.update(current_dict)

        elif _i == 2:
            # last-link-down-time / last-link-up-time / link-downs
            current_dict    = parse_interface_detail(comando)
            vm_dict_info.update(current_dict)
        elif _i == 3:
            # name / apn-profiles / network-mode
            current_dict    = parse_interface_lte_detail(comando)
            vm_dict_info.update(current_dict)
        elif _i == 4:
            # latitude, longitude, altitude
            current_dict    = parse_gps_data(comando)
            vm_dict_info.update(current_dict)
    
    return vm_dict_info


# Funcion para deestructurar el output del commando: "/interface/lte/ print detail"
def parse_interface_lte_detail(message: str) -> dict:
    parse_dict = {}
    patterns = {
        "name": r'name="([^"]+)"',
        "apn-profiles": r"apn-profiles=([^\s]+)",
        "network-mode": r"network-mode=([^\s]+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, message)
        if not match:
            return None  # LTE interface not found
        parse_dict[key] = match.group(1) if match else None  # Assign None if not found

    return parse_dict


# Funcion para deestructurar el output del commando: '/interface/lte/at-chat [find] input="AT\$GPSACP"'
def parse_gps_data(output):
    try:
        # Remove the prefix and split the string by commas
        parts = output.split(":")[1].strip().split(",")

        # Extract the required values
        latitude    = parts[1].strip()
        longitude   = parts[2].strip()
        height      = parts[3].strip()

        return {
            "altitud": latitude,
            "longitud": longitude,
            "altura": height
        }

    except (IndexError, ValueError) as e:
        return {}


# Funcion para realizar un merge de los diccionarios ssh y snmp obtenidos
def extraer_claves(diccionarios_fuente, mapeo_claves):
    nuevo_diccionario = {}
    for idx, diccionario in enumerate(diccionarios_fuente):
        if idx in mapeo_claves:  # Verifica si hay claves asignadas a este diccionario fuente
            for clave in mapeo_claves[idx]:
                if clave in diccionario:
                    nuevo_diccionario[clave] = diccionario[clave]
    return nuevo_diccionario


# Funcion para extraer del diccionario las llaves "indices" del diccionario
def extraer_indices_dictionary(diccionario_fuente : dict) -> dict:
    return_dict = {}
    for key, value in diccionario_fuente.items():
        try:
            index_value = int(key)
            return_dict[index_value] = value
        except: 
            continue
    return return_dict


## Funcion para obtener data de un equipo Mikrotik por subprocess y terminal (conexion SSH)
def parse_LTE_Mikrotik_dictionary(data_ssh_list : dict = {}) -> dict:
    data_dict = {}
    for key_command, result_command in data_ssh_list.items():
        if "/interface/lte/monitor" in key_command:
            # pin-status / registration-status / functionality / manufacturer / model
            data_dict.update( parse_interface_lte_monitor_once(result_command) )
        elif "/interface print" in key_command:
            # last-link-down-time / last-link-up-time / link-downs
            data_dict.update( parse_interface_detail(result_command) )
        elif "/interface/lte/ print" in key_command:
            # name / apn-profiles / network-mode
            data_dict.update( parse_interface_lte_detail(result_command) ) 
        elif "/interface/lte/at-chat" in key_command:
            # latitude, longitude, altitude
            if "error" in result_command.lower():
                continue
            data_dict.update( parse_gps_data(result_command) )
        else:
            continue
    return data_dict


# Parsing la respuesta del programa C en formato json
def extract_command_outputs(salida_json: str) -> list:
    outputs = []
    lines = salida_json.splitlines()

    current_output = []
    for line in lines:
        if line.startswith("•"):
            if current_output:
                outputs.append("\n".join(current_output).strip() or None)
                current_output = []
        else:
            current_output.append(line)

    # Append the last output if any
    if current_output:
        outputs.append("\n".join(current_output).strip() or None)

    return outputs


# Ejecutar el programa en C y capturar la salida para datos por terminal (conexion ssh)
def get_ip_lte_ssh(ip_remote    : str, 
                   fullpath_script : str, 
                   usuario      : str = "test", 
                   contraseña   : str = "test",
                   timeout_ssh  : int = 15) -> list:
    responde_in_ssh = ""
    json_output = {}

    try:
        # Medir el tiempo de inicio        
        resultado = subprocess.run(
            [fullpath_script, ip_remote, usuario, contraseña],
            capture_output = True,
            text    = True,
            check   = True,
            timeout = timeout_ssh  # Esperar un máximo de 15 segundos
        )

        #print(resultado.stdout)
        #print(resultado.stderr)

        # Preprocesar la salida para corregir secuencias de escape
        responde_in_ssh = resultado.stdout
        
        dict_res = procesar_salida(responde_in_ssh)
        json_output.update(dict_res)

    except subprocess.CalledProcessError as e:
        pass
        #print(f"Error {ip_remote} al ejecutar el programa en C: {e}")
    except json.JSONDecodeError as e:
        pass
        #print(f"Error {ip_remote} al decodificar la salida JSON: {e}")
    except subprocess.TimeoutExpired:
        pass
        #print(f"Error {ip_remote} Timeout Expired: {e}")
    finally:
        return json_output


if __name__ == "__main__":
    ip_test = "192.168.2.159"
    test_user = "admin"
    test_pass = "HCG"

    data = get_ip_lte_ssh(
        ip_remote = ip_test,
        fullpath_script = "/usr/smartlink/LTE/ssh_LTE_request",
        usuario = test_user,
        contraseña = test_pass
    )

    print(data)

