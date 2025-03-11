from fastapi import APIRouter, HTTPException, Query, Path, Depends
from datetime import datetime
from typing import Optional, List
from connection import get_db_connection
from mariadb import IntegrityError

from routes.__utils__ import (
    insert_data,
    insert_bulk_data,
    fetch_data_with_dates
)
from models.servidor_models import Servidor

router = APIRouter()

@router.post("/add")
async def add_servidor(servidor: Servidor, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "servidor_data", servidor)

@router.post("/add_list")
async def add_servidor_list(list_model: List[Servidor], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "servidor_data", list_model, Servidor.model_fields.keys())

@router.get("/get", summary="Obtener datos de servidor de la base de datos por rangos de tiempo y con paginación")
async def get_servidor(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar")
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "servidor_data", start_date, end_date, limit, offset)
