from fastapi import APIRouter, HTTPException, Path, Query

from mariadb import IntegrityError
from models.LTE_data_models import LTE
from datetime import datetime, timedelta
from typing import Optional, List
from models.LTE_data_models import LTE
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination

router = APIRouter()

@router.post("/add")
def add_servidor(servidor: LTE):
    return insert_data("LTE_data", servidor)

@router.post("/add_list")
def add_servidor_list(list_model: List[LTE]):
    return insert_bulk_data("LTE_data", list_model, LTE.model_fields.keys())


'''
@router.get("/get", summary="Obtener datos LTE por rango de fechas y con paginación")
def get_lte_data(
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM LTE_data WHERE 1=1"
        params = []
        if start_date:
            query += " AND fecha >= %s"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= %s"
            params.append(end_date)
        query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cursor.execute(query, params)

        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al obtener los datos LTE: {str(e)}")
    finally:
        conn.close()
    

@router.get("/get_ip/{ip}", summary="Obtener datos LTE por IP con rango de fechas y paginación")
def get_lte_data_by_ip(
    ip: str = Path(..., description="Dirección IP del equipo"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM LTE_data WHERE ip = %s"
        params = [ip]
        if start_date:
            query += " AND fecha >= %s"
            params.append(start_date)
        if end_date:
            query += " AND fecha <= %s"
            params.append(end_date)
        query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cursor.execute(query, params)

        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al obtener los datos LTE: {str(e)}")
    finally:
        conn.close()
'''