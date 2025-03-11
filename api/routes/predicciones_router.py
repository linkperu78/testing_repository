from fastapi import APIRouter, HTTPException, Query, Path, Depends
from datetime import datetime
from typing import Optional, List
from connection import get_db_connection
from mariadb import IntegrityError

from models.predicciones_models import Predicciones
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination

router = APIRouter()

@router.post("/add")
async def add_prediccion(prediccion: Predicciones, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "predicciones", prediccion)

@router.post("/add_list")
async def add_prediccion_list(list_model: List[Predicciones], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "predicciones", list_model, Predicciones.model_fields.keys())

@router.get("/get", summary="Obtener datos de predicciones de la base de datos por rangos de tiempo y con paginación")
async def get_prediccion(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar")
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "predicciones", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de predicciones de la base de datos por IP, por rangos de tiempo y con paginación")
async def get_prediccion_by_ip(
    ip: str = Path(..., description="Dirección IP a filtrar"),
    conn_dep=Depends(get_db_connection),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar")
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn, "predicciones", "ip", ip, start_date, end_date, limit, offset)
