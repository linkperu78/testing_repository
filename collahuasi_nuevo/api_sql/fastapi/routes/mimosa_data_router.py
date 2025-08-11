from fastapi import APIRouter, Query, Path, Depends
from typing import Optional, List

from connection import get_db_connection
from routes.__utils__ import (
    insert_data,
    insert_bulk_data,
    fetch_data_with_dates,
    fetch_data_with_single_filter_and_datetime,
    fetch_data_with_filter_and_pagination,
)
from models.mimosa_data_models import MimosaData

router = APIRouter()

@router.post("/add")
async def add_mimosa(mimosa_data: MimosaData):
    return insert_data("mimosa_data", mimosa_data)

@router.post("/add_list")
async def add_mimosa_list(list_model: List[MimosaData]):
    return insert_bulk_data("mimosa_data", list_model, MimosaData.model_fields.keys())

@router.get("/get", summary="Obtener datos de equipos mimosa por rango de fechas y con paginación")
async def get_mimosa(
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    return fetch_data_with_dates("mimosa_data", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de equipos mimosa por IP, rango de fechas y con paginación")
async def get_mimosa_by_ip(
    ip: str = Path(..., description="Dirección IP del dispositivo"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    return fetch_data_with_filter_and_pagination("mimosa_data", "ip", ip, start_date, end_date, limit, offset)

@router.get("/get/{column}/{filter_operator}/{filter_value}", summary="Obtener datos de equipos mimosa por columna y valor de filtro. Tiene rango de fechas opcional y paginación.")
async def get_mimosa_by_column(
    column: str = Path(..., description="Nombre de la columna a filtrar"),
    filter_operator: str = Path(..., description="Operador de comparación para el filtro"),
    filter_value: str = Path(..., description="Valor a filtrar"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    return fetch_data_with_single_filter_and_datetime("mimosa_data", column, filter_operator, filter_value, start_date, end_date, limit, offset)

'''
@router.post("/add")
async def add_mimosa(mimosa_data: MimosaData, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "mimosa_data", mimosa_data)

@router.post("/add_list")
async def add_mimosa_list(list_model: List[MimosaData], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "mimosa_data", list_model, MimosaData.model_fields.keys())

@router.get("/get", summary="Obtener datos de equipos mimosa por rango de fechas y con paginación")
async def get_mimosa(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "mimosa_data", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de equipos mimosa por IP, rango de fechas y con paginación")
async def get_mimosa_by_ip(
    conn_dep=Depends(get_db_connection),
    ip: str = Path(..., description="Dirección IP del dispositivo"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn, "mimosa_data", "ip", ip, start_date, end_date, limit, offset)

@router.get("/get/{column}/{filter_operator}/{filter_value}", summary="Obtener datos de equipos mimosa por columna y valor de filtro. Tiene rango de fechas opcional y paginación.")
async def get_mimosa_by_column(
    conn_dep=Depends(get_db_connection),
    column: str = Path(..., description="Nombre de la columna a filtrar"),
    filter_operator: str = Path(..., description="Operador de comparación para el filtro"),
    filter_value: str = Path(..., description="Valor a filtrar"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    async with conn_dep as conn:
        return fetch_data_with_single_filter_and_datetime(conn, "mimosa_data", column, filter_operator, filter_value, start_date, end_date, limit, offset)
'''

