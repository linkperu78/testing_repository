from fastapi import APIRouter, HTTPException, Query, Path, Depends
from datetime import datetime
from typing import Optional, List, Dict
import json

from connection import get_db_connection
from routes.__utils__ import (
    insert_data,
    insert_bulk_data,
    fetch_data_with_dates,
    fetch_data_with_single_filter_and_datetime,
    fetch_data_with_filter_and_pagination,
)
from models.cambium_data_models import CambiumData

router = APIRouter()

@router.post("/add")
async def add_cambium(cambium_data: CambiumData, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "cambium_data", cambium_data)

@router.post("/add_list")
async def add_cambium_list(list_model: List[CambiumData], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "cambium_data", list_model, CambiumData.model_fields.keys())

@router.get("/get", summary="Obtener datos de equipos Cambium por rango de fechas y con paginación")
async def get_cambium(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "cambium_data", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de equipos Cambium por IP, rango de fechas y con paginación")
async def get_cambium_by_ip(
    conn_dep=Depends(get_db_connection),
    ip: str = Path(..., description="Dirección IP del dispositivo"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación"),
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn, "cambium_data", "ip", ip, start_date, end_date, limit, offset)

@router.get("/get/{column}/{filter_operator}/{filter_value}", summary="Obtener datos de equipos Cambium por columna y valor de filtro. Tiene rango de fechas opcional y paginación.")
async def get_cambium_by_column(
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
        return fetch_data_with_single_filter_and_datetime(conn, "cambium_data", column, filter_operator, filter_value, start_date, end_date, limit, offset)


