from fastapi import APIRouter, Request, HTTPException, Query, Path
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
import json

from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination
from models.sensores_models import Sensor


router = APIRouter()
### SENSORES

@router.post("/add")
def add_sensor(sensor: Sensor):
    return insert_data("sensores", sensor)

@router.post("/add_list")
def add_sensor_list(sensores: list[Sensor]):
    return insert_bulk_data("sensores", sensores, Sensor.model_fields.keys())

@router.get("/get", summary="Obtener datos de sensores por rango de fechas y con paginación")
def get_sensores(
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    return fetch_data_with_dates("sensores", start_date, end_date, limit, offset)


@router.get("/get_ip/{ip}", summary="Obtener un sensor por su dirección IP. Permite filtrar por rango de fechas y tiene paginación")
def get_sensor_by_ip(
    ip: str = Path(..., description="Dirección IP del sensor"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    return fetch_data_with_filter_and_pagination("sensores", "ip", ip, start_date, end_date, limit, offset)