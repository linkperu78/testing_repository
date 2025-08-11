from fastapi import APIRouter, Request, HTTPException, Query, Path
from datetime import datetime, timedelta
from typing import List
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError

from models.servidor_models import Servidor
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination

router = APIRouter()

@router.post("/add")
def add_servidor(servidor: Servidor):
    return insert_data("servidor_data", servidor)

@router.post("/add_list")
def add_servidor_list(list_model: List[Servidor]):
    return insert_bulk_data("servidor_data", list_model, Servidor.model_fields.keys())

@router.get("/get", summary="Obtener datos de servidor de la base de datos por rangos de tiempo y con paginación")
def get_servidor(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar")
    ):
    return fetch_data_with_dates("servidor_data", start_date, end_date, limit, offset)