## Smartlink - Reestructuracion de la base de Datos
## Version      : V2025.2
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128
## Tables       : Any

import sys
sys.path.append('/usr/smartlink')
from pprint import pprint as pp
import mariadb
import os
import json
import traceback

script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

TABLE_NAME          = "rajant_data"
COLUMN_TO_CHANGE    = "wireless"

##          FUNCIONES PERSONALIZADAS
def transform_wireless_dict(data):
    transformed         = {}
    array_key_filter    = ["peer", "noise", "Bytes"]
    
    peers = []
    for interface, details in data.items():
        transformed[interface] = {}    
        
        for key, value in details.items():
            jump = True
            for a in array_key_filter:
                if a in key:
                    jump = False
        
            if jump:
                continue

            if key.startswith("peer"):
                peers.append(value["cost"])
            else:
                transformed[interface][key] = value
    
    if peers:
        transformed["cost"] = min(peers)

    return transformed


# Connect to MariaDB Platform
if __name__ == "__main__":
    try:
        conn = mariadb.connect(
            user        = "admin",
            password    = "audio2023",
            host        = "localhost",
            port        = 3306,
            database    = "smartlinkDB"
        )
        cursor = conn.cursor()

        print("Conexion Exitosa")

        query = f"SHOW COLUMNS FROM {TABLE_NAME}"
        cursor.execute(query)

        headers_table = [row[0] for row in cursor.fetchall()]
        index_to_change     = headers_table.index(COLUMN_TO_CHANGE) if COLUMN_TO_CHANGE in headers_table else -1
        index_numeric       = headers_table.index("id") if "id" in headers_table else -1
        
        if index_to_change < 0:
            raise Exception(f"No se encontro columna '{COLUMN_TO_CHANGE}'")
        if index_numeric < 0:
            raise Exception("No se encontro columna 'id'")

        query = f"SELECT * FROM {TABLE_NAME} WHERE NOT JSON_CONTAINS_PATH({COLUMN_TO_CHANGE}, 'one', '$.cost')"
        cursor.execute(query)
        results = [ [row[index_numeric], row[index_to_change]] 
                   for row in cursor.fetchall() ]

        query_update = f"UPDATE {TABLE_NAME} SET {COLUMN_TO_CHANGE} = %s WHERE id = %s"
        new_array_data = []
        for _id, _json_str in results:
            data = json.loads(_json_str)
            new_data = transform_wireless_dict(data)
            if _id > 0:
                #pp(new_data)
                new_array_data.append((json.dumps(new_data, ensure_ascii=False), _id))

        #for a in new_array_data: print(a)
        cursor.executemany(query_update, new_array_data)
        conn.commit()

    except mariadb.Error as e:
        print(f"Error in MariaDB Platform: {e}")
        sys.exit(1)

    except Exception as e:
        if str(e):
            print(f" !! {script_name} main function error: {e}")
            print(traceback.format_exc())
    finally:
        if cursor:
            cursor.close()
            conn.close()
