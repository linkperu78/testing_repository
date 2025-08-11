from fastapi import APIRouter, HTTPException, Path, Query
from connection import get_db_connection
from mariadb import IntegrityError
from typing import List, Dict, Any

from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination
from models.ubicacion_gps_models import UbicacionGPS


router = APIRouter()

@router.post("/add", summary="Agregar una ubicación GPS")
def add_ubicacion_gps(ubicacion_gps: UbicacionGPS):
    return insert_data("ubicacion_gps", ubicacion_gps)

@router.post("/add_list", summary="Agregar una lista de ubicaciones GPS")
def add_ubicacion_gps_list(ubicaciones_gps: List[UbicacionGPS]):
    return insert_bulk_data("ubicacion_gps", ubicaciones_gps, UbicacionGPS.model_fields.keys())


@router.get("/get", summary="Obtener ubicaciones GPS por rango de fechas y con paginación")
def get_ubicacion_gps(
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    """Recupera ubicaciones GPS por rango de fechas con soporte de paginación."""
    return fetch_data_with_dates("ubicacion_gps", start_date, end_date, limit, offset)


@router.get("/get_ip/{ip}", summary="Obtener ubicación GPS por IP por rango de fechas y con paginación")
def get_ubicacion_gps_by_ip(
    ip: str = Path(..., description="Dirección IP del dispositivo"),
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    """Recupera ubicaciones GPS por IP y rango de fechas con soporte de paginación."""
    return fetch_data_with_filter_and_pagination("ubicacion_gps", "ip", ip, start_date, end_date, limit, offset)

