import mariadb
import sys

# Configura el pool de conexiones al inicio del módulo
try:
    pool = mariadb.ConnectionPool(
        pool_name   = "mypool",
        pool_size   = 10,
        user        = "admin",
        password    = "audio2023",
        host        = "localhost",
        port        = 3306,
        #database="smartlinktelecom"
        database    = "smartlinkDB"
    )
except mariadb.Error as e:
    print(f"Error creating connection pool: {e}")
    sys.exit(1)

def get_db_connection():
    """Devuelve una conexión del pool."""
    try:
        return pool.get_connection()
    except mariadb.Error as e:
        print(f"Error getting connection from pool: {e}")
        sys.exit(1)
