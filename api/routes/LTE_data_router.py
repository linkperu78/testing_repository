from fastapi import APIRouter, HTTPException, Path, Query, Depends
from mariadb import IntegrityError
from datetime import datetime
from typing import Optional, List
from models.LTE_data_models import LTE
from connection import get_db_connection
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination

router = APIRouter()

@router.post("/add")
async def add_servidor(servidor: LTE, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "LTE_data", servidor)

@router.post("/add_list")
async def add_servidor_list(list_model: List[LTE], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn, "LTE_data", list_model, LTE.model_fields.keys())

'''
@router.get("/get", summary="Obtener datos LTE por rango de fechas y con paginación")
async def get_lte_data(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "LTE_data", start_date, end_date, limit, offset)
'''

'''
@router.get("/get_ip/{ip}", summary="Obtener datos LTE por IP con rango de fechas y paginación")
async def get_lte_data_by_ip(
    ip: str = Path(..., description="Dirección IP del equipo"),
    conn_dep=Depends(get_db_connection),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn, "LTE_data", "ip", ip, start_date, end_date, limit, offset)
'''
