from fastapi import APIRouter, Request, HTTPException, Query, Path
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
from typing import List, Dict
import json

from routes.__utils__ import insert_data, insert_bulk_data,fetch_data_with_dates, fetch_data_with_single_filter_and_datetime
from models.cambium_data_models import CambiumData




router = APIRouter()

@router.post("/add")
def add_cambium(cambium_data: CambiumData):
    return insert_data("cambium_data", cambium_data)

@router.post("/add_list")
def add_cambium_list( list_model: List[CambiumData] ):
    return insert_bulk_data("cambium_data", list_model, CambiumData.model_fields.keys())


@router.get("/get", summary="Obtener datos de equipos Cambium por rango de fechas y con paginación")
def get_cambium(
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    return fetch_data_with_dates("cambium_data", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de equipos Cambium por IP, rango de fechas y con paginación")
def get_cambium_by_ip(
    ip: str = Path(..., description="Dirección IP del dispositivo"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM cambium_data WHERE ip = %s"
        params = [ip]

        if start_date:
            query += " AND fecha >= %s"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= %s"
            params.append(end_date)
        
        query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columnas = [desc[0] for desc in cursor.description]
        cambium_data = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        return cambium_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos de resultados de cambium_data por IP: {str(e)}")
    finally:
        conn.close()

@router.get("/get/{column}/{filter_operator}/{filter_value}", summary="Obtener datos de equipos Cambium por columna y valor de filtro. Tiene rango de fechas opcional y paginación.")
def get_cambium_by_column(
    column: str = Path(..., description="Nombre de la columna a filtrar"),
    filter_operator: str = Path(..., description="Operador de comparación para el filtro"),
    filter_value: str = Path(..., description="Valor a filtrar"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    return fetch_data_with_single_filter_and_datetime("cambium_data", column, filter_operator, filter_value, start_date, end_date, limit, offset)



