from fastapi import APIRouter, HTTPException, Query, Path, Depends
from datetime import datetime
from connection import get_db_connection
from typing import Optional, List
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination
from models.eventos_models import Evento

router = APIRouter()

@router.post("/add", summary="Agregar un evento")
async def add_evento(evento: Evento, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn=conn, table="eventos", model=evento)

@router.post("/add_list", summary="Agregar una lista de eventos")
async def add_evento_list(eventos: List[Evento], conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_bulk_data(conn=conn, table="eventos", data=eventos, columns=Evento.model_fields.keys())

@router.get("/get", summary="Obtener eventos con filtro por fecha y paginación")
async def get_eventos(
    conn_dep=Depends(get_db_connection),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn=conn, table="eventos", start_date=start_date, end_date=end_date, limit=limit, offset=offset, round_to_quarter_hour=False)

@router.get("/get_ip/{ip}", summary="Obtener eventos por IP con filtro de fecha y paginación")
async def get_eventos_by_ip(
    ip: str = Path(..., description="Dirección IP del evento"),
    conn_dep=Depends(get_db_connection),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn=conn, table="eventos", ip_column="ip", ip=ip, start_date=start_date, end_date=end_date, limit=limit, offset=offset)
