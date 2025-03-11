from contextlib import asynccontextmanager
import mariadb
import sys
import time
import os
import yaml

# Cargar configuracion desde YAML
script_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_dir, "configAPI.yml")

with open(config_path, "r") as ymlfile:
    DB_CONFIG = yaml.safe_load(ymlfile)["database"]

# Configurar pool de conexiones con reintentos
def create_connection_pool():
    retries = 5
    while retries > 0:
        try:
            pool = mariadb.ConnectionPool(
                pool_name="mypool",
                pool_size=DB_CONFIG["pool_size"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                database=DB_CONFIG["database"],
                pool_reset_connection=False
            )
            return pool
        except mariadb.Error as e:
            retries -= 1
            print(f"Error al conectar a la base de datos: {e}. Reintentando en 5 segundos...")
            time.sleep(5)

    print("No se pudo conectar a la base de datos despues de varios intentos.")
    sys.exit(1)

# Inicializar el pool de conexiones
pool = create_connection_pool()

@asynccontextmanager
async def get_db_connection():
    """Obtiene una conexion del pool y la cierra automaticamente despues de su uso."""
    conn = None
    try:
        conn = pool.get_connection()
        
        # Verifica si la conexion sigue activa
        cursor = conn.cursor()
        cursor.execute("SELECT 1")  # Verifica que la conexion siga viva

        yield conn
    except mariadb.Error as e:
        print(f"Error al obtener conexion: {e}")
        raise e
    finally:
        if conn:
            conn.close()  # Asegura que la conexion se cierre correctamente
