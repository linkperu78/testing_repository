import traceback
import json
import os

## Obtenemos el diccionario para obtener el Manufacturer
script_dir  = os.path.dirname(os.path.abspath(__file__))
json_path   = os.path.join(script_dir, "manufacturer.json")
with open(json_path, "r") as f:
    manufacturers = json.load(f)

def convert_mac_hex_to_readable(byte_mac: str, add_manufac: bool = False):
    #byte_mac = raw_mac_str.encode("latin1")
    readable_mac = ':'.join(f'{b:02X}' for b in byte_mac)
    if add_manufac:
        prefix = readable_mac[:8]  # First 3 bytes as string
        manufacturer_name = manufacturers.get(prefix, "Unknown")
        return readable_mac, manufacturer_name
    return readable_mac


## GPS conversion from "X.XXN, Y.YYW" to "float, float"
def dms_to_dd(dms_str) -> float:
    direction = dms_str[-1]
    _dms = float(dms_str[:-1])
    degrees = int(_dms / 100)
    minutes = (_dms % 100) / 60
    dd = degrees + minutes
    
    if direction in ['S', 'W']:
        dd *= -1  # Invert the result for South and West directions
    return round(dd,7)


## Extraccion del pool de datos de rajant
def extract_rajant_model_data(data_proto_rajant) -> list:
    rajant_dictionary   = {}
    wired_array_ip_cost = []

    try:
        #  - - - > Si hay datos GPS se almacenan
        if data_proto_rajant.HasField("gps") and (gps_data := data_proto_rajant.gps.gpsPos).ListFields():
            rajant_dictionary["gps"] = {
                "latitud"   : dms_to_dd(gps_data.gpsLat),
                "longitud"  : dms_to_dd(gps_data.gpsLong),
                "altitud"   : round(float(gps_data.gpsAlt), 2)
            }

        # - - - >  Valores del sistema / sensores
        if data_proto_rajant.HasField("system"):
            data_system = data_proto_rajant.system
            sensor_dictionary = {
                "info": {
                    "sysTemperatura": data_system.temperature,
                    "modelo": data_proto_rajant.manufacturer.model
                },
                "valores": {
                    sensor_type: [data.value.current for data in getattr(data_system.sensors, sensor_type)]
                    for sensor_type in data_system.sensors.DESCRIPTOR.fields_by_name
                    if hasattr(data_system.sensors, sensor_type)
                }
            }
            rajant_dictionary["sensores"] = sensor_dictionary

        # - - - >  Obtenemos los valores de configuracion del equipo
        rajant_dictionary["config"] = {"uptime": data_system.uptime}

        # - - - >  Obtenemos los datos Instamesh
        instamesh_fields = ["packetsDropped", "packetsMulticast", "packetsReceived", "packetsSent"]
        rajant_dictionary["instamesh"] = {
            field: getattr(data_proto_rajant.instamesh, field) for field in instamesh_fields
        }

        # - - - >  Obtenemos los valores de Wired
        fields_wired_stats          = ["rxBytes", "txBytes"]
        final_wired_dictionary      = {}
        # Valores de cada interfaz "wired" que existan
        # SOLAMNETE si estos contienen modo "AptMaster"
        for _wired_data in data_proto_rajant.wired:
            #print(f"IP = {data_proto_rajant.system.ipv4.address} / {_wired_data.aptState}")
            if int(_wired_data.aptState) != 0:
                continue
            # Valor de Costo        //       Extraemos solo el costo si tiene APT_MASTER
            for _peer_data in _wired_data.peer:
                if _peer_data.HasField("cost"):
                    wired_array_ip_cost.append([_peer_data.ipv4Address, int(_peer_data.cost)])    
            
            stats_data  = _wired_data.stats
            wired_stats = {field: getattr(stats_data, field) for field in fields_wired_stats}
            final_wired_dictionary[_wired_data.name] = wired_stats
        rajant_dictionary["wired"] = final_wired_dictionary

        # - - - > Obtenemos los valores de Wireless
        fields_wireless             = ["noise", "channel"]      
        fields_wireless_stats       = ["rxBytes", "txBytes"]
        fields_rptArp               = ["mac", "action", "cost", "ipv4Address", "encapId"]
        final_wireless_dictionary   = {}
        
        for _wireless_data in data_proto_rajant.wireless:   # Todos los datos wireless en data.proto
            name_wireless = _wireless_data.name
            clientes = []
            for _client in _wireless_data.ap:
                ssid_name = _client.essid
                for _client_data in _client.client:
                    mac_value, manufacturer_value = convert_mac_hex_to_readable(_client_data.mac, True)
                    clientes.append({
                        "mac"       : mac_value,
                        "type"      : manufacturer_value,
                        "rate"      : _client_data.rate,
                        "rssi"      : _client_data.rssi,
                        "signal"    : _client_data.signal,
                        "ssid"      : ssid_name
                    })
            wireless_dict = {
                **{field: getattr(_wireless_data, field) for field in fields_wireless},
                **{field: getattr(_wireless_data.stats, field) for field in fields_wireless_stats}
            }   # Almacenamos en un diccionario (TODO: deberia ser un array para minimizar espacio)
            if clientes:
                wireless_dict["clients"] = clientes

            final_wireless_dictionary[name_wireless] = wireless_dict
            wireless_costs = [ int(peer.cost) for peer in _wireless_data.peer if peer.HasField("cost") ]

        if wireless_costs:
            final_wireless_dictionary["cost"] = min(wireless_costs)

        #  - - - - - - - - - > Obtenemos los valores de rptArp 
        if hasattr(data_proto_rajant.system, 'rptPeer'):
            rpt_data = data_proto_rajant.system.rptPeer
            rpt_dict = {}
            for field in fields_rptArp:
                if hasattr(rpt_data, field):
                    rpt_dict[field] = (
                        convert_mac_hex_to_readable(getattr(rpt_data, field))
                        if field == "mac"
                        else getattr(rpt_data, field)
                    )
            final_wireless_dictionary["rpt"] = rpt_dict
        rajant_dictionary["wireless"] = final_wireless_dictionary

    except Exception as e:
        print(f"Error al encontrar el valor en el data Rajant:\n{e}")
        if False:
            print(traceback.format_exc())

    return [rajant_dictionary, wired_array_ip_cost]


# Leer el archivo de texto y procesar las listas de servidores y clientes
def get_server_clients_from_file(file_path : str) -> dict:
    ip_dict = {}
    current_server = None
    current_section = None

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line == "[Servidor]":
                current_section = "server"
            elif line == "[Clientes]":
                current_section = "clients"
            else:
                if current_section == "server":
                    current_server = line
                    ip_dict[current_server] = []
                elif current_section == "clients" and current_server:
                    ip_dict[current_server].append(line)

    return ip_dict




