from fastapi import APIRouter, Request, HTTPException, Query, Path
from datetime import datetime, timedelta
from typing import List
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
from fastapi import Body

from models.latencia_models import Latencia
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination

router = APIRouter()

@router.post("/add")
def add_latencia(latencia: Latencia):
    return insert_data("latencia", latencia)

@router.post("/add_list")
def add_latencia_list(list_model: List[Latencia]):
    return insert_bulk_data("latencia", list_model, Latencia.model_fields.keys())



@router.get("/get", summary="Obtener datos de latencia de la base de datos por rangos de tiempo y con paginación")
def get_latencia(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
    round_dates: Optional[bool] = Query(False, description="Redondear la fecha a la hora más cercana")
):
    return fetch_data_with_dates("latencia", start_date, end_date, limit, offset, round_dates)
        

@router.get("/get_ip/{ip}", summary="Obtener datos de latencia de la base de datos por IP, por rangos de tiempo y con paginación")
def get_latencia_by_ip(
    ip: str = Path(..., description="Dirección IP de la latencia"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    return fetch_data_with_filter_and_pagination("latencia", "ip", ip, start_date, end_date, limit, offset)

@router.get("/get_poor_latency", summary="Obtener datos de latencia mayores a 100 ms, con rango de fechas, paginación y opción de aproximar la fecha al cuarto de hora")
def get_poor_latency(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
    aprox_date: bool = Query(False, description="Si es True, redondea la columna fecha al cuarto de hora más cercano")
):
    """
    Recupera registros de latencia mayores a 100ms.
    Si aprox_date es True, la columna 'fecha' se redondea al cuarto de hora.
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        params = []

        # ✅ Selección de columnas con o sin redondeo
        if aprox_date:
            select = "SELECT id, ip, latencia, FROM_UNIXTIME(ROUND(UNIX_TIMESTAMP(fecha) / 900) * 900) AS fecha, fecha_DB"
        else:
            select = "SELECT *"

        base_query = f"{select} FROM latencia WHERE latencia > 100"

        if start_date:
            base_query += " AND fecha >= %s"
            params.append(start_date)
        if end_date:
            base_query += " AND fecha <= %s"
            params.append(end_date)

        base_query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(column_names, row)) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")
    finally:
        conn.close()




@router.get("/get_fechadb", summary="Obtener datos de latencia de la base de datos por rangos de tiempo y con paginación")
def get_latencia(
    start_date: datetime = Query(..., description="Fecha de inicio de la consulta (obligatoria, formato: YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="Fecha de fin de la consulta (obligatoria, formato: YYYY-MM-DD)"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar")
):
    """Función genérica para recuperar datos con paginación."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"SELECT * FROM latencia WHERE 1=1"
        params = []

        if start_date:
            query += " AND fecha_DB >= %s"
            params.append(start_date)
        if end_date:
            query += " AND fecha_DB <= %s"
            params.append(end_date)

        query += " ORDER BY fecha_DB DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")
    finally:
        conn.close()
        
from fastapi import Body

@router.delete("/delete", summary="Eliminar datos de latencia desde una fecha específica (por defecto, hace 7 días)")
def delete_latencia_from_date(
    from_date: Optional[datetime] = Query(
        default_factory=lambda: datetime.now() - timedelta(days=7),
        description="Fecha desde la cual eliminar registros (por defecto, hace 7 días)"
    )
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        delete_query = "DELETE FROM latencia WHERE fecha >= %s"
        cursor.execute(delete_query, (from_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        return {"message": f"{deleted_count} registros eliminados desde {from_date}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar los datos: {str(e)}")
    finally:
        conn.close()


@router.put("/update", summary="Actualizar un registro de latencia por IP y fecha")
def update_latencia_by_ip_and_date(
    ip: str = Query(..., description="Dirección IP del registro a actualizar"),
    fecha: datetime = Query(..., description="Fecha exacta del registro a actualizar"),
    latencia: Latencia = Body(..., description="Nuevos datos del registro")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        update_query = """
            UPDATE latencia
            SET ip = %s, latencia = %s, fecha = %s, fecha_DB = %s
            WHERE ip = %s AND fecha = %s
        """
        values = (
            latencia.ip, latencia.latencia, latencia.fecha, latencia.fecha_DB, ip, fecha
        )
        cursor.execute(update_query, values)
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Registro no encontrado con esa IP y fecha")

        return {"message": f"Registro con IP {ip} y fecha {fecha} actualizado correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el registro: {str(e)}")
    finally:
        conn.close()

