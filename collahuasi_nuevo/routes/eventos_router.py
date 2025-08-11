from fastapi import APIRouter, Request, HTTPException, Query, Path
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
import json

router = APIRouter()

from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates,fetch_data_with_filter_and_pagination
from models.eventos_models import Evento

@router.post("/add")
def add_evento(evento: Evento):
    return insert_data("eventos", evento)

@router.post("/add_list")
def add_evento_list(eventos: list[Evento]):
    return insert_bulk_data("eventos", eventos, Evento.model_fields.keys())

@router.get("/get")
def get_eventos(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    return fetch_data_with_dates("eventos", start_date, end_date, limit=limit, offset=offset, round_dates=False)
@router.get("/get_ip/{ip}")
def get_eventos_by_ip(
    ip: str = Path(..., description="Dirección IP del evento"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    return fetch_data_with_filter_and_pagination("eventos", "ip", ip, start_date, end_date, limit=limit, offset=offset)