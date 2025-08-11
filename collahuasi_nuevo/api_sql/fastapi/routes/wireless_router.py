from fastapi import APIRouter, HTTPException, Path, Query
from connection import get_db_connection
from mariadb import IntegrityError
from typing import List, Dict, Any
import json

router = APIRouter()

@router.get("/get", summary="Obtener datos de wireless de Rajant Data con JSON desestructurado. Permite filtrar por fecha y tiene paginación")
def get_wireless_data(
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
) -> List[Dict]:
    """
    Obtiene los campos `ip`, `fecha` y el contenido desestructurado de `wireless`.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener ip, fecha y el campo JSON wireless
        query = """SELECT ip, fecha, wireless FROM rajant_data WHERE 1=1 """
        params = []
        if start_date:
            query += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND fecha <= %s "
            params.append(end_date)
        params.extend([limit, offset])
        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"

        cursor.execute(query, tuple(params))
        columnas = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Proceso para desestructurar el JSON del campo wireless
        results = []
        for row in rows:
            row_dict = dict(zip(columnas, row))
            wireless_data = row_dict.pop("wireless", None)  # Obtén el campo JSON wireless
            if wireless_data:
                try:
                    desestructurado = json.loads(wireless_data)  # Convierte el JSON a un diccionario
                    row_dict.update(desestructurado)  # Combina el JSON con los demás datos
                except json.JSONDecodeError:
                    row_dict["wireless_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al agregar el usuario: {str(e)}")
    finally:
        conn.close()

@router.get("/get_ip/{ip}", summary="Obtener datos wireless de rajant data por su dirección IP. Permite filtrar por rango de fechas y tiene paginación")
def get_wireless_by_ip(
    ip: str = Path(..., description="Dirección IP del sensor"),
    start_date: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: str = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
) -> List[Dict]:
    """
    Obtiene los campos `ip`, `fecha` y el contenido desestructurado de `wireless` para una dirección IP.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para obtener ip, fecha y el campo JSON wireless
        query = """SELECT ip, fecha, wireless FROM rajant_data WHERE ipv4 = %s """
        params = [ip]
        if start_date:
            query += "AND fecha >= %s "
            params.append(start_date)
        if end_date:
            query += "AND fecha <= %s "
            params.append(end_date)
        params.extend([limit, offset])
        query += "ORDER BY fecha DESC LIMIT %s OFFSET %s"

        cursor.execute(query, tuple(params))
        columnas = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Proceso para desestructurar el JSON del campo wireless
        results = []
        for row in rows:
            row_dict = dict(zip(columnas, row))
            wireless_data = row_dict.pop("wireless", None)  # Obtén el campo JSON wireless
            if wireless_data:
                try:
                    desestructurado = json.loads(wireless_data)  # Convierte el JSON a un diccionario
                    row_dict.update(desestructurado)  # Combina el JSON con los demás datos
                except json.JSONDecodeError:
                    row_dict["wireless_error"] = "Error al decodificar JSON"
            results.append(row_dict)

        return results
    except IntegrityError as e:
        raise HTTPException(status_code=422, detail=f"Error de integridad: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al agregar el usuario: {str(e)}")