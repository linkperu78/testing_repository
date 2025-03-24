## Smartlink - Captura de datos de Servidor
## Version      : V2025.2
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128
## Tables       : servidor_data
import sys
sys.path.append('/usr/smartlink')
from api_sql.fastapi.models.servidor_models     import Servidor as Model
from concurrent.futures import ThreadPoolExecutor
from datetime           import datetime
from globalHCG          import *

import paramiko
import traceback    
import subprocess
import queue
import re
import os

script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Direccion de archivos de salida en /usr/smartlink/outputs
TIPO                = "servidor"
SNMP_TIMEOUT        = 10
DB_INVENTARIO_URL   = DB_API_URL + "inventario/get"
URL_POST_MODEL      = DB_API_URL + f"{TIPO}/add_list"
log_file            = os.path.join(FOLDER_OUTPUT, f"{TIPO}_data.csv")

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

# Funcion para obtener datos de Maquinas Virtuales por SSH
def getMVfromServerIP( ip_server : str ) -> dict:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    vm_info = {}

    try:
        client.connect(ip_server, username="root", password="C@ligula2019", port=22, timeout=10)
        _, stdout, _ = client.exec_command("vim-cmd vmsvc/getallvms")
        output = stdout.read().decode('utf-8')

        if not output:
            return {}

        # Process the VM list
        lines = output.strip().split("\n")[1:]  # Skip header line
        for line in lines:
            parts = line.split()
            if not parts:
                continue
            try:
                vm_id = int(parts[0])
                vm_info[vm_id] = {}
                vm_info[vm_id]["name"] = parts[1]
            except ValueError:
                continue  # Ignore malformed lines

        # Fetch summary for all VMs
        total_mv = 0
        for vm_id in vm_info.keys():
            _, stdout, _    = client.exec_command(f"vim-cmd vmsvc/get.summary {vm_id}")
            summary_output  = stdout.read().decode('utf-8')
            total_mv        += 1

            # Extract parameters using regex
            params = {
                #"hostMemoryUsage": re.search(r"hostMemoryUsage\s*=\s*(\d+)", summary_output),
                "MemoriaFisico": re.search(r"memorySizeMB\s*=\s*(\d+)", summary_output),
                "MemoriaActual": re.search(r"guestMemoryUsage\s*=\s*(\d+)", summary_output),
                "CPUActual": re.search(r"overallCpuUsage\s*=\s*(\d+)", summary_output),
                "CPUFisico": re.search(r"numCpu\s*=\s*(\d+)", summary_output),
                "DiscoActual": re.search(r"committed\s*=\s*(\d+)", summary_output),
                "DiscoFisico": re.search(r"uncommitted\s*=\s*(\d+)", summary_output),
            }

            # Convert extracted values to integers or floats
            for key, match in params.items():
                if match:
                    # Divide by 1073741824 for "committed" and "uncommitted" to convert to GB
                    if "committed" in key or "uncommitted" in key:
                        value = float(match.group(1)) / 1073741824
                    else:
                        value = int(match.group(1))
                    vm_info[vm_id][key] = value
                else:
                    vm_info[vm_id][key] = None  # If no match, store None


        vm_info["num_mv"] = total_mv
        return vm_info

    except paramiko.ssh_exception.NoValidConnectionsError:
        print(f"Error: Unable to connect to {ip_server} on port 22. Connection refused.")
    except paramiko.AuthenticationException:
        print(f"Error: Authentication failed for {ip_server}. Check your username/password.")
    except paramiko.SSHException as e:
        print(f"General SSH error with {ip_server}: {e}")
    except Exception as e:
        print(f"Unexpected error with {ip_server}: {e}")
    finally:
        client.close()

    return {}
    
def parse_cpu_info(output: str) -> list:
    cpus = []
    sections = output.split("\n\n")  # CPUs are separated by empty lines
    for section in sections:
        cpu_info = {}
        for line in section.split("\n"):
            match = re.match(r"(\S+):\s*(.+)", line)
            if match:
                key, value = match.groups()
                cpu_info[key] = value.strip()
        if cpu_info:
            cpus.append(cpu_info)
    return cpus

def parse_memory_info(output: str) -> dict:
    memory_info = {}
    for line in output.split("\n"):
        match = re.match(r"(\S+):\s*(.+)", line)
        if match:
            key, value = match.groups()
            memory_info[key] = value.strip()
    return memory_info

def parse_ipmi_sensors(output: str) -> dict:
    ipmi_data = {}
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) >= 2:
            sensor_name = parts[0]
            sensor_value = " ".join(parts[1:])
            ipmi_data[sensor_name] = sensor_value
    return ipmi_data

def getResourcesofServer(ip_server: str) -> dict:
    comandos =  [
        "ps -s", 
        "esxcli hardware cpu list", 
        "esxcli hardware memory get", 
        "vim-cmd vmsvc/getallvms", 
        "esxcli hardware ipmi sdr list", 
        "uptime"
    ]
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    resource_info = {}

    try:
        client.connect(ip_server, username="root", password="C@ligula2019", port=22)
        # Execute each command and store results
        for cmd in comandos:
            _, stdout, _ = client.exec_command(cmd)
            output = stdout.read().decode('utf-8').strip()
            
            if not output:  # Handle case where command output is empty
                output = "No output"
            
            # Add results to dictionary based on the command executed
            if "ps -s" in cmd:
                resource_info["procesos"]   = output
            elif "cpu list" in cmd:
                resource_info["cpu"]        = parse_cpu_info(output)
            elif "memory get" in cmd:
                resource_info["memoria"]    = parse_memory_info(output)
            elif "ipmi sdr list" in cmd:
                resource_info["sensores"]   = parse_ipmi_sensors(output)
            elif "uptime" in cmd:
                resource_info["uptime"]     = output.strip()
            elif "getallvms" in cmd:
                resource_info["mvs"]        = output

        return resource_info

    except paramiko.ssh_exception.NoValidConnectionsError:
        print(f"Error: Unable to connect to {ip_server} on port 22. Connection refused.")
        return {}
    except paramiko.AuthenticationException:
        print(f"Authentication failed for {ip_server}. Check your username/password.")
        return {}
    except paramiko.SSHException as e:
        print(f"General SSH error with {ip_server}: {e}")
        return {}
    finally:
        client.close()

def getSnmpDataOfServer(ip_server : str, community : str = "public") -> dict:
    snmp_list = [
        ['sysDescr'       , '1.3.6.1.2.1.1.1'],
        ['sysUpTime'      , '1.3.6.1.2.1.1.3'],
        ['ifIndex'        , '1.3.6.1.2.1.2.2.1.1'], 
        ['ifDescr'        , '1.3.6.1.2.1.2.2.1.2'],
        ['ifMtu'          , '1.3.6.1.2.1.2.2.1.4'],
        ['ifSpeed'        , '1.3.6.1.2.1.2.2.1.5'],
        ['ifOperStatus'   , '1.3.6.1.2.1.2.2.1.8'],
        ['ifInUcastPkts'  , '1.3.6.1.2.1.2.2.1.11'],
        ['ifOutUcastPkts' , '1.3.6.1.2.1.2.2.1.17']
    ]

    interface_data = {}
    result_dict = {}

    for oid_name, oid in snmp_list:
        string_timeout = f"{SNMP_TIMEOUT}"
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
            result = subprocess.run(command, capture_output = True, text = True, check = True, timeout = SNMP_TIMEOUT + 2).stdout.strip()
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

            else:
                for i, value in enumerate(values):
                    index = str(i + 1)  # Assuming indexes are sequential
                    if index in interface_data:
                        interface_data[index][oid_name] = value
                        
        except subprocess.CalledProcessError:
            result_dict[oid_name] = None
        except subprocess.TimeoutExpired:
            #print(f"Timeout: SNMP request for {oid} on {ip_server} took too long. Skipping...")
            break
            
    result_dict.update(interface_data) 

    return result_dict

def async_task(ip_device, queue : queue.Queue):
    data_resource   = getResourcesofServer(ip_device)
    data_mv         = getMVfromServerIP(ip_device)  if data_resource else {}
    data_snmp       = getSnmpDataOfServer(ip_device)

    if not data_resource and not data_snmp:
        return
    
    #print(f" -> {ip_device} / Data Resource =\n{data_resource}\n")
    #print(f" -> {ip_device} / Data MV =\n{data_mv}\n")
    #print(f" -> {ip_device} / Data SNMP =\n{data_snmp}\n")

    num_mvs = data_mv.get("num_mvs", 0)
    
    ## Convertimos los sub-diccionarios de los indices a un solo sub-diccionario
    # Data MV
    indices_mv_dict     = extraer_indices_dictionary(data_mv)
    final_mv_dict       = {
        'index'     : list(indices_mv_dict.values())
    } 

    # Data SNMP
    indices_snmp_dict   = extraer_indices_dictionary(data_snmp)
    array_snmp_dict     = list(indices_snmp_dict.values())
    final_snmp_dict     = {
        'sysDescr'  : data_snmp.get('sysDescr'),
        'sysUpTime' : data_snmp.get('sysUpTime'),
        'index'     : array_snmp_dict
    }

    # Diccionario para MODEL
    result_dict = {
        "ip"            : ip_device,
        "fecha"         : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "num_mv"        : num_mvs,
        "info_mv"       : final_mv_dict,
        "info_server"   : data_resource,
        "info_snmp"     : final_snmp_dict
    }

    queue.put(result_dict)


##  ---------------------------    PROGRAMA PRINCIAPAL     ---------------------------
try:
    ## Obtenemos datos de la lista de equipos RAJANT de la API
    filter_inventario   = ["tipo", TIPO]
    subscribers         = [ item["ip"] for item in get_request_to_url_with_filters(DB_INVENTARIO_URL, filtrer_array = filter_inventario) ]
    print(f"Se han detectado un total de {len(subscribers)} equipos tipo Servidor en Inventario")
    

    q = queue.Queue()
    max_threads_number = 25

    list_groups_ip_to_request = group_ips(subscribers, max_group_size = max_threads_number)
    once = True

    with ThreadPoolExecutor(max_threads_number) as executor:
        for _group in list_groups_ip_to_request:
            futures = [executor.submit(async_task, _ip, q) for _ip in _group]
            
            # Esperar a que todos los hilos del grupo terminen
            for future in futures:
                future.result()

            # Procesar los resultados inmediatamente
            model_array_list = []
            while not q.empty():
                json_data   = q.get()
                model_array_list.append(Model(**json_data))

            if model_array_list:
                if once:
                    once = False
                    restart_log_file(log_file, Model)
                post_request_to_url_model_array(URL_POST_MODEL, array_model_to_post = model_array_list)
                write_log_files(log_file, model_array_list)

except Exception as e:
    if str(e):
        print(f" ✘ ✘ ERROR en {script_name}:\n{e}")
        #print(" > Error Details:")
        #print(traceback.format_exc())
