from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional, List, Dict
import json
import pandas as pd

from connection import get_db_connection

router = APIRouter()

@router.get("/get", summary="Obtener datos de instamesh con JSON desestructurado. Permite filtrar por fecha y tiene paginación")
async def get_instamesh_data(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
) -> List[Dict]:
    async with conn_dep as conn:
        cursor = conn.cursor()
        query = """SELECT ip, fecha, instamesh FROM rajant_data WHERE 1=1 """
        params = []
        if start_date:
            query += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND fecha <= %s "
            params.append(end_date)
        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        columnas = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(zip(columnas, row))
            instamesh_data = row_dict.pop("instamesh", None)
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)
                    row_dict.update(desestructurado)
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results

@router.get("/get_ip/{ip}", summary="Obtener datos de instamesh para una IP con JSON desestructurado. Permite filtrar por fecha y tiene paginación")
async def get_instamesh_data_by_ip(
    conn_dep=Depends(get_db_connection),
    ip: str = Path(..., description="Dirección IP de la latencia"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
) -> List[Dict]:
    async with conn_dep as conn:
        cursor = conn.cursor()
        query = """SELECT ip, fecha, instamesh FROM rajant_data WHERE ip = %s """
        params = [ip]
        if start_date:
            query += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND fecha <= %s "
            params.append(end_date)
        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        columnas = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(zip(columnas, row))
            instamesh_data = row_dict.pop("instamesh", None)
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)
                    row_dict.update(desestructurado)
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results

@router.get("/get_latencia/", summary="Obtener datos con merge de instamesh y latencia. Permite filtrar por fecha.")
async def get_instamesh_data_with_latencia(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
    clean_data: bool = Query(False, description="Si es True, solo devuelve registros con latencia no nula"),
) -> List[Dict]:
    async with conn_dep as conn:
        cursor = conn.cursor()

        # Consulta SQL
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

        # Ejecutar la consulta
        cursor.execute(query, params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Convertir manualmente los resultados en una lista de diccionarios
        results = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            instamesh_data = row_dict.pop("instamesh", None)
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)
                    row_dict.update(desestructurado)
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results


@router.get("/get_gps_latencia/", summary="Obtener datos con merge de instamesh, latencia y GPS. Permite filtrar por fecha o con paginación.")
async def get_instamesh_data_with_latencia_and_gps(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
    clean_data: bool = Query(False, description="Si es True, solo devuelve registros con latencia, latitud y longitud no nulos"),
) -> List[Dict]:
    async with conn_dep as conn:
        cursor = conn.cursor()

        # Consulta SQL
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

        # Ejecutar la consulta
        cursor.execute(query, params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Convertir manualmente los resultados en una lista de diccionarios
        results = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            instamesh_data = row_dict.pop("instamesh", None)
            if instamesh_data:
                try:
                    desestructurado = json.loads(instamesh_data)
                    row_dict.update(desestructurado)
                except json.JSONDecodeError:
                    row_dict["instamesh_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results
