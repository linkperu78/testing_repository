from fastapi import APIRouter, HTTPException, Path, Query
from connection import get_db_connection
from mariadb import IntegrityError
from typing import List, Dict, Any

from routes.__utils__ import insert_data, insert_bulk_data
from models.estructura_red_models import EstructuraRed

router = APIRouter()

@router.post("/add", summary="Agregar una estructura de red")
def add_estructura_red(estructura_red: EstructuraRed):
    return insert_data("estructura_red", estructura_red)

@router.post("/add_list", summary="Agregar una lista de estructuras de red")
def add_estructura_red_list(estructuras_red: List[EstructuraRed]):
    """Agrega una lista de estructuras de red con IP fuente y cliente."""
    return insert_bulk_data("estructura_red", estructuras_red, EstructuraRed.model_fields.keys())

@router.get("/get", summary="Obtener todas las estructuras de red. Tiene paginación")
def get_estructura_red(
    limit: int = Query(1000, description="Número máximo de registros por página"), 
    offset: int = Query(0, description="Desplazamiento para paginación")):
    """Recupera todas las estructuras de red con soporte de paginación."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM estructura_red LIMIT %s OFFSET %s"
        cursor.execute(query, [limit, offset])
        columnas = [desc[0] for desc in cursor.description]
        estructura_red = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        return estructura_red
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las estructuras de red: {str(e)}")
    finally:
        conn.close()

@router.get("/get_ip/{ip}", summary="Obtener estructura de red por IP, tanto fuente como cliente. Tiene paginación")
def get_estructura_red_by_ip(
    ip: str = Path(..., description="La IP a buscar"), 
    limit: int = Query(1000, description="Número máximo de registros por página"), 
    offset: int = Query(0, description="Desplazamiento para paginación")):
    """Recupera las estructuras de red donde la IP especificada es la IP fuente o cliente."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM estructura_red WHERE ip_fuente = %s OR ip_cliente = %s LIMIT %s OFFSET %s"
        cursor.execute(query, [ip, ip, limit, offset])
        columnas = [desc[0] for desc in cursor.description]
        estructura_red = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        return estructura_red
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la estructura de red para la IP {ip}: {str(e)}")
    finally:
        conn.close()


@router.get("/get_ip_fuente/{ip_fuente}", summary="Obtener estructura de red por IP fuente. Tiene paginación")
def get_estructura_red_by_fuente(
    ip_fuente: str = Path(..., description="La IP fuente a buscar"), 
    limit: int = Query(1000, description="Número máximo de registros por página"), 
    offset: int = Query(0, description="Desplazamiento para paginación")):
    """Recupera las estructuras de red donde la IP especificada es la IP fuente."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM estructura_red WHERE ip_fuente = %s LIMIT %s OFFSET %s"
        cursor.execute(query, [ip_fuente, limit, offset])
        columnas = [desc[0] for desc in cursor.description]
        estructura_red = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        return estructura_red
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la estructura de red para la IP fuente {ip_fuente}: {str(e)}")
    finally:
        conn.close()

@router.get("/get_ip_cliente/{ip_cliente}", summary="Obtener estructura de red por IP cliente. Tiene paginación")
def get_estructura_red_by_cliente(
    ip_cliente: str = Path(..., description="La IP cliente a buscar"), 
    limit: int = Query(1000, description="Número máximo de registros por página"), 
    offset: int = Query(0, description="Desplazamiento para paginación")):
    """Recupera las estructuras de red donde la IP especificada es la IP cliente."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM estructura_red WHERE ip_cliente = %s LIMIT %s OFFSET %s"
        cursor.execute(query, [ip_cliente, limit, offset])
        columnas = [desc[0] for desc in cursor.description]
        estructura_red = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        return estructura_red
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la estructura de red para la IP cliente {ip_cliente}: {str(e)}")
    finally:
        conn.close()