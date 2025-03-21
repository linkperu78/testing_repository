from fastapi import APIRouter, HTTPException, Path, Query, Depends
from connection import get_db_connection
from mariadb import IntegrityError
from typing import List, Dict
import json

router = APIRouter()

@router.get("/get", summary="Obtener datos de wired de Rajant Data con JSON desestructurado. Permite filtrar por fecha y tiene paginación")    
async def get_wired_data(
    conn_dep=Depends(get_db_connection),
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
) -> List[Dict]:
    """
    Obtiene los campos `ip`, `fecha` y el contenido desestructurado de `wired`.
    """
    async with conn_dep as conn:
        try:
            cursor = conn.cursor()

            query = """SELECT ip, fecha, wired FROM rajant_data WHERE 1=1 """
            params = []
            if start_date:
                query += "AND fecha >= %s "
                params.append(start_date)
            if end_date:
                query += "AND fecha <= %s "
                params.append(end_date)
            query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, tuple(params))
            columnas = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            results = []
            for row in rows:
                row_dict = dict(zip(columnas, row))
                wired_data = row_dict.pop("wired", None)
                if wired_data:
                    try:
                        desestructurado = json.loads(wired_data)
                        row_dict.update(desestructurado)
                    except json.JSONDecodeError:
                        row_dict["wired_error"] = "Error al decodificar JSON"
                results.append(row_dict)

            return results

        except IntegrityError as e:
            raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")

@router.get("/get_ip/{ip}", summary="Obtener datos wired de Rajant Data por IP. Permite filtrar por rango de fechas y paginación")
async def get_wired_by_ip(
    ip: str = Path(..., description="Dirección IP del sensor"),
    conn_dep=Depends(get_db_connection),
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
) -> List[Dict]:
    """
    Obtiene datos wired de `rajant_data` filtrando por IP, rango de fechas y paginación.
    """
    async with conn_dep as conn:
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM rajant_data WHERE ip = %s"
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
            columnas = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            results = []
            for row in rows:
                row_dict = dict(zip(columnas, row))
                wired_data = row_dict.pop("wired", None)
                if wired_data:
                    try:
                        desestructurado = json.loads(wired_data)
                        row_dict.update(desestructurado)
                    except json.JSONDecodeError:
                        row_dict["wired_error"] = "Error al decodificar JSON"
                results.append(row_dict)

            return results

        except IntegrityError as e:
            raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener los datos wired: {str(e)}")
