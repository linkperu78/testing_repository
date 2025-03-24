import re
import paramiko
import subprocess
import json

# Funcion para deestructurar el output del commando: "/interface/lte/monitor lte1 once"
def parse_interface_lte_monitor_once(message: str) -> dict:
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
        #print(row)
        if 'type="lte"' in row:
            #print(row)
            message = row

    key_value_pairs = re.findall(r'(\S+?)="([^"]+)"', message)  # For quoted values
    non_quoted_pairs = re.findall(r'(\S+?)=([^\s]+)', message)  # For non-quoted values
    #print(key_value_pairs)
    #print(non_quoted_pairs)

    # Populate the dictionary with both quoted and non-quoted key-value pairs
    for key, value in key_value_pairs + non_quoted_pairs:
        # Remove quotes from the key if present
        key = key.replace('"', '')
        # Clean up the key and value (remove leading/trailing whitespaces if any)
        lte_dict[key] = value.strip()

    #print(lte_dict)
    return lte_dict

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
        latitude = parts[1].strip()
        longitude = parts[2].strip()
        height = parts[3].strip()  # Adjust if needed (some formats may use index 4 for altitude)

        return {
            "altitud": latitude,
            "longitud": longitude,
            "altura": height
        }

    except (IndexError, ValueError) as e:
        #print(f"Error parsing GPS data: {e}")
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

# Funcion para obtener data SNMP de un equipo Mikrotik por subprocess
def getSnmpData(ip_server : str, community : str = "public", timeout : int = 5) -> dict:
    snmp_list = [
        ['sysDescr'         ,   '1.3.6.1.2.1.1.1'],
        ['sysUpTime'        ,   '1.3.6.1.2.1.1.3'],
        ['ifIndex'          ,   '1.3.6.1.2.1.2.2.1.1'], 
        ['ifDescr'          ,   '1.3.6.1.2.1.2.2.1.2'],
        ['ifMtu'            ,   '1.3.6.1.2.1.2.2.1.4'],
        ['ifSpeed'          ,   '1.3.6.1.2.1.2.2.1.5'],
        ['ifOperStatus'     ,   '1.3.6.1.2.1.2.2.1.8'],
        ['ifInUcastPkts'    ,   '1.3.6.1.2.1.2.2.1.11'],
        ['ifOutUcastPkts'   ,   '1.3.6.1.2.1.2.2.1.17'],
        ['RXBytes'          ,   '1.3.6.1.2.1.2.2.1.10'],
        ['TXBytes'          ,   '1.3.6.1.2.1.2.2.1.16']
    ]

    interface_data  = {}
    result_dict     = {}
    indexes_found   = []

    for oid_name, oid in snmp_list:
        string_timeout = f"{timeout}"
        command = [
            "snmpwalk",
            "-v", "2c",
            "-c", community,
            "-Oqv",
            "-t", string_timeout,  # Set SNMP timeout to 10 seconds
            ip_server,
            oid
        ]

        try:
            result = subprocess.run(command, capture_output = True, text = True, check = True, timeout = timeout + 2).stdout.strip()
            values = result.split("\n") if result else []
            if oid_name == 'sysDescr':
                result_dict[oid_name] = values[0] if values else None
            elif oid_name == 'sysUpTime':
                days, hours, minutes, seconds = values[0].replace(".00", "").split(":")
                formatted_str = f"{days}D, {hours}H, {minutes}M, {seconds}S"
                csv_format = f"{days},{hours},{minutes},{seconds}"
                result_dict[oid_name] = [formatted_str, csv_format]
            elif oid_name == 'ifIndex':
                for index in values:
                    interface_data[index] = {}
                    indexes_found.append(index)
            #elif "XBytes" in oid_name :
                #pass
            else:
                for i, value in enumerate(values):
                    #print(f"- {i} / {value}")
                    index = indexes_found[i]
                    if index in interface_data:
                        interface_data[index][oid_name] = value#[index]

        except subprocess.CalledProcessError:
            result_dict[oid_name] = None

        except subprocess.TimeoutExpired:
            #print(f"Timeout: SNMP request for {oid} on {ip_server} took too long. Skipping...")
            break
            
    result_dict.update(interface_data) 

    return result_dict

# Funcion para obtener data de un equipo Mikrotik por subprocess y terminal (conexion SSH)
def getSshData(ip_server : str, _user : str = 'test', _pass : str = 'test', timeout : int = 10, _mode_debug = True) -> dict:
    command_ssh_list = [
        '/interface/lte/monitor lte1 once',
        '/interface print detail',
        '/interface/lte/ print detail',
        '/interface/lte/at-chat [find] input="AT\$GPSACP"'
    ]
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    vm_dict_info = {}
    try:
        #print(f"Conectandose a {ip_server} con {_user} / {_pass} por SSH \n")
        client.connect(ip_server, username = _user.strip(), password = _pass.strip(), port = 22, timeout = timeout,
                       allow_agent=False, look_for_keys=False)
        
        for _i, _comm in enumerate(command_ssh_list, 1):

            _, stdout, stderr = client.exec_command(_comm)
            output  = stdout.read().decode('utf-8').strip()
            error   = stderr.read().decode('utf-8').strip()
            
            if error:
                continue
            
            if not output:
                continue

            if _i == 1:
                # pin-status / registration-status / functionality / manufacturer / model
                current_dict    = parse_interface_lte_monitor_once(output)
                vm_dict_info.update(current_dict)
            elif _i == 2:
                # last-link-down-time / last-link-up-time / link-downs
                current_dict    = parse_interface_detail(output)
                vm_dict_info.update(current_dict)
            elif _i == 3:
                # name / apn-profiles / network-mode
                current_dict    = parse_interface_lte_detail(output)
                vm_dict_info.update(current_dict)
            elif _i == 4:
                # latitude, longitude, altitude
                if "error" in output.lower():
                    continue
                current_dict    = parse_gps_data(output)
                vm_dict_info.update(current_dict)

        client.close()
        return vm_dict_info

    except paramiko.ssh_exception.NoValidConnectionsError:
        if _mode_debug:
            print(f"Error: Unable to connect to {ip_server} on port 22. Connection refused.")
    except paramiko.AuthenticationException:
        if _mode_debug:
            print(f"Error: Authentication failed for {ip_server}. Check your username/password.")
    except paramiko.SSHException as e:
        if _mode_debug:
            print(f"General SSH error with {ip_server}: {e}")
    except Exception as e:
        if _mode_debug:
            print(f"Unexpected error with {ip_server}: {e}")
    finally:
        client.close()
        #print(traceback.format_exc())
        return {}

# Parsing la respuesta del programa C en formato json
def procesar_salida(output):
    comandos = output.strip().split("\n->")  # Dividimos la salida por cada comando

    vm_dict_info = {}
    for _i, comando in enumerate(comandos, 1):
        comando = comando.strip()

        # Si el comando comienza con '->', lo eliminamos
        if comando.startswith("/"):
            comando = comando[1:]

        # Ahora separamos el comando y la respuesta
        lines = comando.split("\n•")
        
        # Extraemos el comando y la respuesta
        output = "\n".join(line.strip() for line in lines[1:]).strip()  # La respuesta es todo lo demás
        
        if _i == 1:
            # pin-status / registration-status / functionality / manufacturer / model
            current_dict    = parse_interface_lte_monitor_once(output)
            vm_dict_info.update(current_dict)

        elif _i == 2:
            # last-link-down-time / last-link-up-time / link-downs
            current_dict    = parse_interface_detail(output)
            vm_dict_info.update(current_dict)
        elif _i == 3:
            # name / apn-profiles / network-mode
            current_dict    = parse_interface_lte_detail(output)
            vm_dict_info.update(current_dict)
        elif _i == 4:
            # latitude, longitude, altitude
            current_dict    = parse_gps_data(output)
            vm_dict_info.update(current_dict)
    
    return vm_dict_info

# Ejecutar el programa en C y capturar la salida para datos por terminal (conexion ssh)
def get_ip_lte_ssh(ip_remote : str, fullpath_script : str, usuario : str = "test", contraseña : str = "test", delay_max : int = 15) -> dict:
    json_output = {}
    try:
        # Medir el tiempo de inicio        
        resultado = subprocess.run(
            [fullpath_script, ip_remote, usuario, contraseña],
            capture_output = True,
            text    = True,
            check   = True,
            timeout = delay_max  # Esperar un máximo de 15 segundos
        )

        # Preprocesar la salida para corregir secuencias de escape
        salida_json = resultado.stdout
        json_output.update(procesar_salida(salida_json))        
    
    except subprocess.CalledProcessError as e:
        pass
        #print(f"Error {ip_remote} al ejecutar el programa en C: {e}")
    except json.JSONDecodeError as e:
        pass
        #print(f"Error {ip_remote} al decodificar la salida JSON: {e}")
    except subprocess.TimeoutExpired:
        pass
    finally:
        # Medir el tiempo de finalización
        return json_output

