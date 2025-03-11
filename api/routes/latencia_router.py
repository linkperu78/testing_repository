from fastapi import APIRouter, HTTPException, Query, Path, Depends
from datetime import datetime
from typing import List, Optional
from connection import get_db_connection
from mariadb import IntegrityError
from models.latencia_models import Latencia
from routes.__utils__ import (
    insert_data,
    insert_bulk_data,
    fetch_data_with_dates,
    fetch_data_with_filter_and_pagination,
)

router = APIRouter()

@router.post("/add")
async def add_latencia(latencia: Latencia, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "latencia", latencia)

@router.post("/add_list")
async def add_latencia_list(list_model: List[Latencia], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "latencia", list_model, Latencia.model_fields.keys())

@router.get("/get", summary="Obtener datos de latencia de la base de datos por rangos de tiempo y con paginación")
async def get_latencia(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
    round_dates: Optional[bool] = Query(False, description="Redondear la fecha a la hora más cercana")
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "latencia", start_date, end_date, limit, offset, round_dates)

@router.get("/get_ip/{ip}", summary="Obtener datos de latencia de la base de datos por IP, por rangos de tiempo y con paginación")
async def get_latencia_by_ip(
    ip: str = Path(..., description="Dirección IP de la latencia"),
    conn_dep=Depends(get_db_connection),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn, "latencia", "ip", ip, start_date, end_date, limit, offset)

@router.get("/get_poor_latency", summary="Obtener datos de latencia mayores a 100 ms, con rango de fechas y paginación")
async def get_poor_latency(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    async with conn_dep as conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM latencia WHERE latencia > 100"
            params = []

            if start_date:
                query += " AND fecha >= %s"
                params.append(start_date)
            if end_date:
                query += " AND fecha <= %s"
                params.append(end_date)

            query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(column_names, row)) for row in rows]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")

@router.get("/get_fechadb", summary="Obtener datos de latencia por rangos de tiempo y con paginación")
async def get_latencia_by_fechadb(
    conn_dep=Depends(get_db_connection),
    start_date: datetime = Query(..., description="Fecha de inicio de la consulta (obligatoria, formato: YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="Fecha de fin de la consulta (obligatoria, formato: YYYY-MM-DD)"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    async with conn_dep as conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM latencia WHERE fecha_DB BETWEEN %s AND %s ORDER BY fecha_DB DESC LIMIT %s OFFSET %s"
            params = [start_date, end_date, limit, offset]

            cursor.execute(query, params)
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(column_names, row)) for row in rows]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")
