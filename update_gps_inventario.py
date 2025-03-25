## Smartlink - Actualiza los valores gps
## Version      : V2025.2
## Author       : HCG-Group, Area de Backend
## Contacto     : Anexo 3128
## Tables       : Latencia
from datetime   import datetime as dt

import sys
import mariadb
import json
import traceback
import queue
import os

script_path         = os.path.abspath(__file__)
script_folder       = os.path.dirname(script_path)
script_name         = os.path.basename(script_path)


##  ---------------------------    FUNCIONES     ---------------------------
TABLE_INVENTARIO = "inventario"
COLUMN_TO_CHANGE = "gps"
COLUMN_TO_FILTER = "anotacion"
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

        ## Obtenemos de inventario las filas que contengan drive
        query = f"SHOW COLUMNS FROM {TABLE_INVENTARIO}"
        cursor.execute(query)

        headers_table = [row[0] for row in cursor.fetchall()]
        index_to_change     = headers_table.index(COLUMN_TO_CHANGE) if COLUMN_TO_CHANGE in headers_table else -1
        index_reference     = headers_table.index(COLUMN_TO_FILTER) if COLUMN_TO_FILTER in headers_table else -1
        index_ip            = headers_table.index("ip") if "ip" in headers_table else -1

        
        if index_to_change < 0:
            raise Exception(f"No se encontro columna '{COLUMN_TO_CHANGE}'")
        if index_reference < 0:
            raise Exception(f"No se encontro columna '{COLUMN_TO_FILTER}'")
        if index_ip < 0:
            raise Exception("No se encontro columna 'id'")

        query = f"SELECT * FROM {TABLE_INVENTARIO} WHERE JSON_CONTAINS_PATH({COLUMN_TO_FILTER}, 'one', '$.gps') = 1"
        cursor.execute(query)
        
        results = []
        for row in cursor.fetchall():
            try:
                json_data = json.loads(row[index_reference]) if isinstance(row[index_reference], str) else row[index_reference]
                results.append({
                    "ip": row[index_ip],
                    "ip_gps": json_data.get("gps", None),
                    "gps" : {}
                })
            except (json.JSONDecodeError, TypeError):
                print(f"Advertencia: No se pudo procesar la fila con IP {row[index_ip]}")


        ips_to_search = [r["ip_gps"] for r in results if r["ip_gps"]]
        if not ips_to_search:
            print("No hay IPs con GPS para buscar.")
            sys.exit(0)


        # Buscar el último registro GPS para cada ip_gps
        query = f"""
            SELECT ip, latitud, longitud, altitud
            FROM ubicacion_gps
            WHERE ip IN ({', '.join(['%s'] * len(ips_to_search))})
            AND fecha = (
                SELECT MAX(fecha)
                FROM ubicacion_gps AS sub
                WHERE sub.ip = ubicacion_gps.ip
            );
        """
        cursor.execute(query, ips_to_search)

        # Crear un diccionario con los datos GPS
        gps_data = {row[0]: {"latitud": row[1], "longitud": row[2], "altitud": row[3]} for row in cursor.fetchall()}

        filtered_results = [
            {
                "ip": r["ip"],
                "ip_gps": r["ip_gps"],
                "gps": gps_data[r["ip_gps"]]
            }
            for r in results if r["ip_gps"] in gps_data
        ]

        update_query = f"""
            UPDATE {TABLE_INVENTARIO}
            SET {COLUMN_TO_CHANGE} = %s
            WHERE ip = %s;
        """

        # Ejecutar el UPDATE para cada registro en 'filtered_results'
        for record in filtered_results:
            gps_content = json.dumps(record["gps"])  # Contenido de la llave "gps"
            ip_value = record["ip"]                  # IP correspondiente

            if gps_content == "{}":
                continue  # No actualiza si no hay contenido GPS válido

            try:
                cursor.execute(update_query, (gps_content, ip_value))
            except Exception as e:
                print(f"Error al actualizar la IP {ip_value}: {e}")
                
        # Confirmar los cambios
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


