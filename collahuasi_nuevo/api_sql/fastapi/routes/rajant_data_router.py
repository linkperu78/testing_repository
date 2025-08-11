from fastapi import APIRouter, HTTPException, Path, Query
from connection import get_db_connection
from mariadb import IntegrityError
from typing import List, Dict, Any
import pandas as pd
import json

from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination, round_to_nearest_15_minutes
from models.rajant_data_models import RajantData

router = APIRouter()

@router.post("/add", summary="Agregar datos de red Rajant")
def add_rajant_data(rajant_data: RajantData):
    return insert_data("rajant_data", rajant_data)

@router.post("/add_list", summary="Agregar muchos datos de red Rajant")
def add_rajant_data_list(list_model: List[RajantData]):
    """Agrega una lista de datos de red Rajant con información de nodos y enlaces."""
    return insert_bulk_data("rajant_data", list_model, RajantData.model_fields.keys())

@router.get("/get", summary="Obtener datos de red Rajant por rango de fechas y con paginación")
def get_rajant_data(
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    return fetch_data_with_dates("rajant_data", start_date, end_date, limit, offset)


@router.get("/get_ip/{ip}", summary="Obtener datos de red Rajant por IP, por rango de fechasy con paginación opcional")
def get_rajant_data_by_ip(
    ip: str = Path(..., description="La dirección IP a buscar"),
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    """Recupera datos de red Rajant por IP con soporte de rango de fechas y paginación."""
    return fetch_data_with_filter_and_pagination("rajant_data", "ip", ip, start_date, end_date, limit, offset)


@router.get("/get_latencia", summary="Obtener datos red Rajant por rango de fechas y con paginación haciendo left join con tabla de latencia")
def get_rajant_data_with_latencia(
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
) -> List[Dict]:
    """
    Obtiene datos de `rajant_data` e `instamesh` junto con `latencia`, redondeando las fechas al minuto más cercano.
    """
    try:
        conn = get_db_connection()

        # Consultar los datos de `rajant_data`
        query_rajant = """SELECT * FROM rajant_data WHERE 1=1 """
        params = []
        if start_date:
            query_rajant += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query_rajant += "AND fecha <= %s "
            params.append(end_date)
        query_rajant += "ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        rajant_data = pd.read_sql_query(query_rajant, conn, params=params)

        # Consultar los datos de `latencia`
        query_latencia = """SELECT ip, fecha, latencia FROM latencia WHERE 1=1 """
        params = []
        if start_date:
            query_latencia += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query_latencia += "AND fecha <= %s "
            params.append(end_date)
        query_latencia += "ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        latencia_data = pd.read_sql_query(query_latencia, conn, params=params)

        rajant_data['fecha'] = pd.to_datetime(rajant_data['fecha']).apply(round_to_nearest_15_minutes)
        latencia_data['fecha'] = pd.to_datetime(latencia_data['fecha']).apply(round_to_nearest_15_minutes)

        # Hacer el merge de los DataFrames
        merged_data = pd.merge(rajant_data, latencia_data, on=['ip', 'fecha'], how='left')

        # Convertir el DataFrame en una lista de diccionarios
        results = []
        for row in merged_data.itertuples(index=False):
            row_dict = dict(row._asdict())
            if pd.isnull(row_dict['latencia']):
                row_dict['latencia'] = None
            results.append(row_dict)

        return results

    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")