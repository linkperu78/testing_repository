from fastapi import APIRouter, HTTPException, Query, Path, Depends
from datetime import datetime
from connection import get_db_connection
from typing import Optional, List
from mariadb import IntegrityError

from routes.__utils__ import (
    insert_data,
    insert_bulk_data,
    fetch_data_with_dates,
    fetch_data_with_filter_and_pagination
)
from models.sensores_models import Sensor

router = APIRouter()

@router.post("/add")
async def add_sensor(sensor: Sensor, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "sensores", sensor)

@router.post("/add_list")
async def add_sensor_list(sensores: List[Sensor], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "sensores", sensores, Sensor.model_fields.keys())

@router.get("/get", summary="Obtener datos de sensores por rango de fechas y con paginación")
async def get_sensores(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "sensores", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener un sensor por su dirección IP. Permite filtrar por rango de fechas y tiene paginación")
async def get_sensor_by_ip(
    ip: str = Path(..., description="Dirección IP del sensor"),
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn, "sensores", "ip", ip, start_date, end_date, limit, offset)
