from fastapi import APIRouter, Request, HTTPException, Query, Path
from datetime import datetime, timedelta
from typing import List
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError

from models.predicciones_models import Predicciones
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination

router = APIRouter()

@router.post("/add")
def add_prediccion(prediccion: Predicciones):
    return insert_data("predicciones", prediccion)

@router.post("/add_list")
def add_prediccion_list(list_model: List[Predicciones]):
    return insert_bulk_data("predicciones", list_model, Predicciones.model_fields.keys())

@router.get("/get", summary="Obtener datos de predicciones de la base de datos por rangos de tiempo y con paginación")
def get_prediccion(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar")
):
    return fetch_data_with_dates("predicciones", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de predicciones de la base de datos por IP, por rangos de tiempo y con paginación")
def get_prediccion_by_ip(
    ip: str = Path(..., description="Dirección IP a filtrar"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar")
):
    return fetch_data_with_filter_and_pagination("predicciones", "ip", ip, start_date, end_date, limit, offset)


