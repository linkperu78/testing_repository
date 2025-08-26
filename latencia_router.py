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


@router.get(
    "/get_latencia_stats",
    summary="Obtener estadísticas de latencia (una fila por IP) con datos de inventario"
)
def get_latencia_stats(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(1000, gt=0, description="Número de registros a mostrar"),
):
    """
    Devuelve UNA fila por IP en el rango dado.
    Incluye:
      - max_latencia, promedio_latencia, min_latencia (>0)
      - total_mediciones, latencia_100_200, latencia_mayor_200
      - desconexiones (latencia <= 0)   # si quieres solo -1, reemplaza por (l.latencia = -1)
      - y datos de inventario (marca, rol, tipo, snmp_conf, anotacion, gps, tag)
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        params = []

        select_columns = """
            l.ip,
            MAX(l.latencia) AS max_latencia,
            AVG(l.latencia) AS promedio_latencia,
            COUNT(l.latencia) AS total_mediciones,
            /* mínimo de latencia considerando solo valores positivos */
            MIN(CASE WHEN l.latencia > 0 THEN l.latencia END) AS min_latencia,
            COUNT(CASE WHEN l.latencia BETWEEN 100 AND 200 THEN 1 END) AS latencia_100_200,
            COUNT(CASE WHEN l.latencia > 200 THEN 1 END) AS latencia_mayor_200,
            /* conteo de desconexiones: latencia <= 0 (o usa = -1 si lo prefieres) */
            COUNT(CASE WHEN l.latencia <= 0 THEN 1 END) AS desconexiones,
            MAX(i.marca) AS marca,
            MAX(i.rol) AS rol,
            MAX(i.tipo) AS tipo,
            MAX(i.snmp_conf) AS snmp_conf,
            MAX(i.anotacion) AS anotacion,
            MAX(i.gps) AS gps,
            MAX(i.tag) AS tag
        """

        base_query = f"""
            SELECT {select_columns}
            FROM latencia l
            LEFT JOIN inventario i ON l.ip = i.ip
            WHERE 1=1
        """

        if start_date:
            base_query += " AND l.fecha >= %s"
            params.append(start_date)
        if end_date:
            base_query += " AND l.fecha <= %s"
            params.append(end_date)

        base_query += " GROUP BY l.ip"

        base_query += """
            ORDER BY latencia_mayor_200 DESC, promedio_latencia DESC, max_latencia DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        results = []
        for row in rows:
            r = dict(zip(column_names, row))
            # Redondeos de presentación
            if r.get("max_latencia") is not None:
                r["max_latencia"] = round(float(r["max_latencia"]), 3)
            if r.get("promedio_latencia") is not None:
                r["promedio_latencia"] = round(float(r["promedio_latencia"]), 3)
            if r.get("min_latencia") is not None:
                r["min_latencia"] = round(float(r["min_latencia"]), 3)
            results.append(r)

        # Total de IPs distintas en el rango
        count_query = """
            SELECT COUNT(DISTINCT l.ip)
            FROM latencia l
            WHERE 1=1
        """
        count_params = []
        if start_date:
            count_query += " AND l.fecha >= %s"
            count_params.append(start_date)
        if end_date:
            count_query += " AND l.fecha <= %s"
            count_params.append(end_date)

        cursor.execute(count_query, count_params)
        total_records = cursor.fetchone()[0] or 0

        return {
            "data": results,
            "total_records": int(total_records),
            "returned_records": len(results),
            "offset": offset,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass

@router.get(
    "/get_latencia_stats",
    summary="Obtener estadísticas de latencia (una fila por IP) con datos de inventario"
)
def get_latencia_stats(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(1000, gt=0, description="Número de registros a mostrar"),
):
    """
    Devuelve UNA fila por IP en el rango dado.
    Incluye:
      - max_latencia
      - promedio_latencia (solo valores >0)
      - min_latencia (solo valores >0)
      - total_mediciones
      - latencia_100_200
      - latencia_mayor_200
      - desconexiones (latencia <=0)
      - y datos de inventario (marca, rol, tipo, snmp_conf, anotacion, gps, tag)
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        params = []

        select_columns = """
            l.ip,
            MAX(l.latencia) AS max_latencia,
            AVG(CASE WHEN l.latencia > 0 THEN l.latencia END) AS promedio_latencia,
            COUNT(l.latencia) AS total_mediciones,
            MIN(CASE WHEN l.latencia > 0 THEN l.latencia END) AS min_latencia,
            COUNT(CASE WHEN l.latencia BETWEEN 100 AND 200 THEN 1 END) AS latencia_100_200,
            COUNT(CASE WHEN l.latencia > 200 THEN 1 END) AS latencia_mayor_200,
            COUNT(CASE WHEN l.latencia <= 0 THEN 1 END) AS desconexiones,
            MAX(i.marca) AS marca,
            MAX(i.rol) AS rol,
            MAX(i.tipo) AS tipo,
            MAX(i.snmp_conf) AS snmp_conf,
            MAX(i.anotacion) AS anotacion,
            MAX(i.gps) AS gps,
            MAX(i.tag) AS tag
        """

        base_query = f"""
            SELECT {select_columns}
            FROM latencia l
            LEFT JOIN inventario i ON l.ip = i.ip
            WHERE 1=1
        """

        if start_date:
            base_query += " AND l.fecha >= %s"
            params.append(start_date)
        if end_date:
            base_query += " AND l.fecha <= %s"
            params.append(end_date)

        base_query += " GROUP BY l.ip"

        base_query += """
            ORDER BY latencia_mayor_200 DESC, promedio_latencia DESC, max_latencia DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        results = []
        for row in rows:
            r = dict(zip(column_names, row))
            # Redondeos de presentación
            if r.get("max_latencia") is not None:
                r["max_latencia"] = round(float(r["max_latencia"]), 3)
            if r.get("promedio_latencia") is not None:
                r["promedio_latencia"] = round(float(r["promedio_latencia"]), 3)
            if r.get("min_latencia") is not None:
                r["min_latencia"] = round(float(r["min_latencia"]), 3)
            results.append(r)

        # Total de IPs distintas
        count_query = """
            SELECT COUNT(DISTINCT l.ip)
            FROM latencia l
            WHERE 1=1
        """
        count_params = []
        if start_date:
            count_query += " AND l.fecha >= %s"
            count_params.append(start_date)
        if end_date:
            count_query += " AND l.fecha <= %s"
            count_params.append(end_date)

        cursor.execute(count_query, count_params)
        total_records = cursor.fetchone()[0] or 0

        return {
            "data": results,
            "total_records": int(total_records),
            "returned_records": len(results),
            "offset": offset,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass


@router.get("/get_latencia_stats_summary", summary="Resumen general de estadísticas de latencia")
def get_latencia_stats_summary(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta")
):
    """
    Resumen global en el período:
      - total_ips                 : IPs distintas con muestras en el rango
      - total_mediciones          : todas las muestras (incluye <=0)
      - total_mediciones_validas  : muestras con latencia > 0
      - promedio_general          : promedio solo de latencias > 0
      - max_global                : máximo (toma cualquier valor, negativos no afectan)
      - min_global                : mínimo solo de latencias > 0
      - desconexiones             : conteo de latencias <= 0  (cambiar a '= -1' si solo quieres -1)
      - mediciones_altas          : latencias > 100 ms (sobre todas)
      - porcentaje_latencia_alta  : (mediciones >100) / (muestras >0) * 100
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        params = []

        summary_query = """
            SELECT 
                COUNT(DISTINCT l.ip) AS total_ips,
                COUNT(l.latencia) AS total_mediciones,
                COUNT(CASE WHEN l.latencia > 0 THEN 1 END) AS total_mediciones_validas,
                AVG(CASE WHEN l.latencia > 0 THEN l.latencia END) AS promedio_general,
                MAX(l.latencia) AS max_global,
                MIN(CASE WHEN l.latencia > 0 THEN l.latencia END) AS min_global,
                COUNT(CASE WHEN l.latencia <= 0 THEN 1 END) AS desconexiones,  -- si quieres solo -1: (l.latencia = -1)
                COUNT(CASE WHEN l.latencia > 100 THEN 1 END) AS mediciones_altas,
                ROUND(
                    (COUNT(CASE WHEN l.latencia > 100 THEN 1 END) * 100.0) 
                    / NULLIF(COUNT(CASE WHEN l.latencia > 0 THEN 1 END), 0)
                , 2) AS porcentaje_latencia_alta
            FROM latencia l
            WHERE 1=1
        """

        if start_date:
            summary_query += " AND l.fecha >= %s"
            params.append(start_date)
        if end_date:
            summary_query += " AND l.fecha <= %s"
            params.append(end_date)

        cursor.execute(summary_query, params)
        column_names = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        result = dict(zip(column_names, row))

        # Redondeos de presentación
        if result.get("promedio_general") is not None:
            result["promedio_general"] = round(float(result["promedio_general"]), 3)
        if result.get("max_global") is not None:
            result["max_global"] = round(float(result["max_global"]), 3)
        if result.get("min_global") is not None:
            result["min_global"] = round(float(result["min_global"]), 3)

        # Si no hubo muestras válidas, porcentaje quedará NULL → opcional: poner 0.0
        if result.get("porcentaje_latencia_alta") is None:
            result["porcentaje_latencia_alta"] = 0.0

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el resumen: {str(e)}")
    finally:
        try:
            conn.close()
        except:
            pass
