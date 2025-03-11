from fastapi import APIRouter, HTTPException, Path, Query, Depends
from typing import List
from connection import get_db_connection
from routes.__utils__ import (
    insert_data,
    insert_bulk_data,
    fetch_data_with_dates,
    fetch_data_with_filter_and_pagination,
)
from models.clustering_data_models import ClusteringData

router = APIRouter()

@router.post("/add", summary="Agregar un dato de clustering")
async def add_clustering_data(clustering_data: ClusteringData, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "clustering_data", clustering_data)

@router.post("/add_list", summary="Agregar una lista de datos de clustering")
async def add_clustering_data_list(clustering_data: List[ClusteringData], conn_dep=Depends(get_db_connection)):
    """Agrega una lista de datos de clustering."""
    async with conn_dep as conn:
        return insert_bulk_data(conn, "clustering_data", clustering_data, ClusteringData.model_fields.keys())

@router.get("/get", summary="Obtener datos de clustering")
async def get_clustering_data(
    conn_dep=Depends(get_db_connection),
    start_date: str = Query(None, description="Fecha de inicio"),
    end_date: str = Query(None, description="Fecha de fin"),
    limit: int = Query(10, description="Número de registros a obtener"),
    offset: int = Query(0, description="Número de registros a omitir"),
):
    async with conn_dep as conn:
        return fetch_data_with_dates(conn, "clustering_data", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de clustering por IP")
async def get_clustering_data_by_ip(
    ip: str = Path(..., description="Dirección IP"),
    conn_dep=Depends(get_db_connection),
    start_date: str = Query(None, description="Fecha de inicio"),
    end_date: str = Query(None, description="Fecha de fin"),
    limit: int = Query(10, description="Número de registros a obtener"),
    offset: int = Query(0, description="Número de registros a omitir"),
):
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn, "clustering_data", "ip", ip, start_date, end_date, limit, offset)
