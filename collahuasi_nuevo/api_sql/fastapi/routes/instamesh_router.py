from fastapi import APIRouter, HTTPException, Path, Query
from connection import get_db_connection
from mariadb import IntegrityError
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
import pandas as pd

from routes.__utils__ import round_to_nearest_15_minutes

router = APIRouter()

@router.get("/get", summary="Obtener datos de instamesh con JSON desestructurado. Permite filtrar por fecha y tiene paginación")	
def get_instamesh_data(
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
) -> List[Dict]:
    """
    Obtiene los campos `ip`, `fecha` y el contenido desestructurado de `instamesh`.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener ip, fecha y el campo JSON instamesh
        query = """SELECT ip, fecha, instamesh FROM rajant_data WHERE 1=1 """
        params = []
        if start_date:
            query += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND fecha <= %s "
            params.append(end_date)
        params.extend([limit, offset])
        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"

        cursor.execute(query, tuple(params))
        columnas = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Proceso para desestructurar el JSON del campo instamesh
        results = []
        for row in rows:
            row_dict = dict(zip(columnas, row))
            instamesh_data = row_dict.pop("instamesh", None)  # Obtén el campo JSON instamesh
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)  # Convierte el JSON a un diccionario
                    row_dict.update(desestructurado)  # Combina el JSON con los demás datos
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results
  
 
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al agregar el usuario: {str(e)}")
    finally:
        conn.close()

@router.get("/get_ip/{ip}", summary="Obtener datos de instamesh para una IP con JSON desestructurado. Permite filtrar por fecha y tiene paginación")
def get_instamesh_data_by_ip(
    ip: str = Path(..., description="Dirección IP de la latencia"),
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
) -> List[Dict]:
    """
    Obtiene los campos `ip`, `fecha` y el contenido desestructurado de `instamesh` para una ip particular. 
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener ip, fecha y el campo JSON instamesh
        query = """SELECT ip, fecha, instamesh FROM rajant_data WHERE ip = %s """
        params = [ip]
        if start_date:
            query += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND fecha <= %s "
            params.append(end_date)
        params.extend([limit, offset])
        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"

        cursor.execute(query, tuple(params))
        columnas = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Proceso para desestructurar el JSON del campo instamesh
        results = []
        for row in rows:
            row_dict = dict(zip(columnas, row))
            instamesh_data = row_dict.pop("instamesh", None)  # Obtén el campo JSON instamesh
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)  # Convierte el JSON a un diccionario
                    row_dict.update(desestructurado)  # Combina el JSON con los demás datos
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results

    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al agregar el usuario: {str(e)}")
    finally:
        conn.close()


@router.get("/get_latencia/", summary="Obtener datos con merge de instamesh y latencia. Permite filtrar por fecha.")
def get_instamesh_data_with_latencia(
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
    clean_data: bool = Query(False, description="Si es True, solo devuelve registros con latencia no nula")
) -> List[Dict]:
    """
    Obtiene datos de `rajant_data` e `instamesh` junto con `latencia`, redondeando las fechas al múltiplo de 15 minutos más cercano.
    """
    try:
        conn = get_db_connection()

        # Construcción dinámica de la consulta SQL
        query = """
        SELECT 
            r.ip, 
            FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(r.fecha) / 900) * 900) AS fecha, 
            r.instamesh, 
            l.latencia
        FROM rajant_data r
        LEFT JOIN latencia l 
            ON r.ip = l.ip 
            AND FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(r.fecha) / 900) * 900) = 
                FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(l.fecha) / 900) * 900)
        WHERE 1=1 
        """
        
        params = []
        if start_date:
            query += "AND r.fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND r.fecha <= %s "
            params.append(end_date)
        if clean_data:
            query += "AND l.latencia IS NOT NULL "

        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Ejecutar consulta
        df = pd.read_sql_query(query, conn, params=params)

        # Procesar el JSON del campo `instamesh`
        results = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            instamesh_data = row_dict.pop("instamesh", None)
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)
                    row_dict.update(desestructurado)
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results

    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        conn.close()

@router.get("/get_gps_latencia/", summary="Obtener datos con merge de instamesh, latencia y GPS. Permite filtrar por fecha o con paginacion.")
def get_instamesh_data_with_latencia_and_gps(
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Numero maximo de registros por pagina"),
    offset: int = Query(0, description="Desplazamiento para paginacion"),
    clean_data: bool = Query(False, description="Si es True, solo devuelve registros con latencia, latitud y longitud no nulos")
) -> List[Dict]:
    """
    Obtiene datos de `rajant_data` e `instamesh` junto con `latencia` y `gps`, redondeando las fechas al multiplo de 15 minutos mas cercano.
    """
    try:
        conn = get_db_connection()

        # Construcci�n din�mica de la consulta SQL
        query = """
        SELECT 
            r.ip, 
            FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(r.fecha) / 900) * 900) AS fecha, 
            r.instamesh, 
            l.latencia, 
            g.latitud, 
            g.longitud
        FROM rajant_data r
        LEFT JOIN latencia l 
            ON r.ip = l.ip 
            AND FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(r.fecha) / 900) * 900) = 
                FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(l.fecha) / 900) * 900)
        LEFT JOIN ubicacion_gps g 
            ON r.ip = g.ip 
            AND FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(r.fecha) / 900) * 900) = 
                FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(g.fecha) / 900) * 900)
        WHERE 1=1 
        """
        
        params = []
        if start_date:
            query += "AND r.fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND r.fecha <= %s "
            params.append(end_date)
        if clean_data:
            query += "AND l.latencia IS NOT NULL AND g.latitud IS NOT NULL AND g.longitud IS NOT NULL "

        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Ejecutar consulta
        df = pd.read_sql_query(query, conn, params=params)

        # Procesar el JSON del campo `instamesh`
        results = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            instamesh_data = row_dict.pop("instamesh", None)
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)
                    row_dict.update(desestructurado)
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results

    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        conn.close()