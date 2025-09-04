from fastapi import APIRouter, Request, HTTPException, Query, Path
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional, List, Dict, Any
from mariadb import IntegrityError
import json
import math

from routes.__utils__ import insert_data, insert_bulk_data,fetch_data_with_dates, fetch_data_with_single_filter_and_datetime
from models.cambium_data_models import CambiumData


router = APIRouter()

# --------------------- Helpers de parseo ---------------------
def _is_num(x: Any) -> bool:
    try:
        f = float(x)
        return not (math.isnan(f) or math.isinf(f))
    except Exception:
        return False

def _to_float_fixed(x: Any) -> Optional[float]:
    """
    Devuelve float solo si x es un número "fijo":
      - int/float válidos -> ok
      - str numérica -> ok
      - str JSON -> si decodifica a número -> ok; si lista/dict -> ignorar
      - lista -> ignorar (None)
      - dict -> ignorar (None) (la extracción por 'metric' se hace en otra función)
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x) if _is_num(x) else None
    if isinstance(x, str):
        xs = x.strip()
        # ¿string numérica?
        if _is_num(xs):
            return float(xs)
        # ¿string JSON?
        try:
            j = json.loads(xs)
        except Exception:
            return None
        # si el JSON decodifica a número, ok; si no, ignorar
        return float(j) if _is_num(j) else None
    # listas/dicts u otros tipos -> ignorar
    return None

def _extract_metric_fixed(raw: Any, key: str) -> Optional[float]:
    """
    Extrae la métrica 'key' (p.ej., 'H', 'V', 'rx') SOLO si termina siendo un número fijo.
    Reglas:
      - raw puede ser número/str-num: si 'key' no aplica, usamos ese número (para casos raros).
      - raw dict/str-JSON-dict: tomamos raw[key] (case-insensitive).
         * si es lista -> ignorar
         * si es num/str-num -> aceptar
      - raw lista/str-JSON-lista -> ignorar
    """
    # Si viene como string, intenta JSON
    if isinstance(raw, str):
        s = raw.strip()
        try:
            raw_json = json.loads(s)
            raw = raw_json
        except Exception:
            # Si no es JSON, puede ser número suelto
            return _to_float_fixed(s)

    if isinstance(raw, dict):
        # buscar key case-insensitive
        val = None
        if key in raw:
            val = raw[key]
        else:
            for k, v in raw.items():
                if str(k).lower() == key.lower():
                    val = v
                    break
        if val is None:
            return None
        # si es lista -> ignorar
        if isinstance(val, list):
            return None
        # si es dict -> no lo usamos
        if isinstance(val, dict):
            return None
        return _to_float_fixed(val)

    if isinstance(raw, list):
        return None  # listas no se consideran

    # número suelto / str-num ya se manejó en _to_float_fixed
    return _to_float_fixed(raw)

def _accumulate(stats: Dict[str, Dict[str, float]], ip: str, val: Optional[float]):
    if val is None:
        return
    s = stats.setdefault(ip, {"count": 0, "sum": 0.0, "min": None, "max": None})
    s["count"] += 1
    s["sum"] += float(val)
    s["min"] = float(val) if s["min"] is None else min(s["min"], float(val))
    s["max"] = float(val) if s["max"] is None else max(s["max"], float(val))

def _finalize(stats: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    out = []
    for ip, s in stats.items():
        avg = (s["sum"] / s["count"]) if s["count"] > 0 else None
        out.append({
            "ip": ip,
            "count": s["count"],
            "avg": None if avg is None else round(avg, 3),
            "min": None if s["min"] is None else round(s["min"], 3),
            "max": None if s["max"] is None else round(s["max"], 3),
        })
    out.sort(key=lambda d: (d["max"] if d["max"] is not None else -1e18), reverse=True)
    return out

# --------------------- Rutas ---------------------
@router.post("/add")
def add_cambium(cambium_data: CambiumData):
    return insert_data("cambium_data", cambium_data)

@router.post("/add_list")
def add_cambium_list( list_model: List[CambiumData] ):
    return insert_bulk_data("cambium_data", list_model, CambiumData.model_fields.keys())


@router.get("/get", summary="Obtener datos de equipos Cambium por rango de fechas y con paginación")
def get_cambium(
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    return fetch_data_with_dates("cambium_data", start_date, end_date, limit, offset)

@router.get("/get_ip/{ip}", summary="Obtener datos de equipos Cambium por IP, rango de fechas y con paginación")
def get_cambium_by_ip(
    ip: str = Path(..., description="Dirección IP del dispositivo"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM cambium_data WHERE ip = %s"
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
        cambium_data = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        return cambium_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los datos de resultados de cambium_data por IP: {str(e)}")
    finally:
        conn.close()

@router.get("/get/{column}/{filter_operator}/{filter_value}", summary="Obtener datos de equipos Cambium por columna y valor de filtro. Tiene rango de fechas opcional y paginación.")
def get_cambium_by_column(
    column: str = Path(..., description="Nombre de la columna a filtrar"),
    filter_operator: str = Path(..., description="Operador de comparación para el filtro"),
    filter_value: str = Path(..., description="Valor a filtrar"),
    start_date: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD"),
    limit: int = Query(1000, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Desplazamiento para paginación")
):
    return fetch_data_with_single_filter_and_datetime("cambium_data", column, filter_operator, filter_value, start_date, end_date, limit, offset)

# --------------------- 1) Stats por IP (genérico) ---------------------
@router.get("/get_metric_stats_by_ip", summary="Estadísticas por IP (SNR_H / SNR_V / RX) filtrando PMP-SM")
def get_metric_stats_by_ip(
    column: str = Query(..., description="Columna origen: 'snr' o 'link_radio'"),
    metric: str = Query(..., description="Métrica: 'H', 'V' o 'rx'"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit_rows: int = Query(200000, ge=1, le=1000000, description="Límite de filas a leer de DB"),
    ip_filter: Optional[str] = Query(None, description="Filtrar por IP exacta (opcional)")
):
    """
    Lee crudo desde cambium_data, LEFT JOIN inventario y filtra i.tipo='PMP-SM'.
    Acepta SOLO valores numéricos fijos (no listas, no dicts anidados, no nulls).
    column ∈ {'snr','link_radio'}, metric ∈ {'H','V','rx'}.
    """
    column = column.strip().lower()
    metric = metric.strip()

    if column not in ("snr", "link_radio"):
        raise HTTPException(status_code=400, detail="column debe ser 'snr' o 'link_radio'")
    if metric.lower() not in ("h", "v", "rx"):
        raise HTTPException(status_code=400, detail="metric debe ser 'H', 'V' o 'rx'")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        q = f"""
            SELECT c.ip, c.fecha, c.{column}
            FROM cambium_data c
            LEFT JOIN inventario i ON c.ip = i.ip
            WHERE i.tipo = 'PMP-SM'
        """
        params: List[Any] = []
        if ip_filter:
            q += " AND c.ip = %s"
            params.append(ip_filter)
        if start_date:
            q += " AND c.fecha >= %s"
            params.append(start_date)
        if end_date:
            q += " AND c.fecha <= %s"
            params.append(end_date)
        q += " ORDER BY c.fecha DESC LIMIT %s"
        params.append(limit_rows)

        cursor.execute(q, params)

        stats: Dict[str, Dict[str, float]] = {}
        processed = 0
        mkey = metric  # mantener mayúsculas/minúsculas que vengan

        for ip, fecha, raw in cursor.fetchall():
            val = _extract_metric_fixed(raw, mkey)
            _accumulate(stats, ip, val)
            processed += 1

        data = _finalize(stats)
        return {
            "column": column,
            "metric": metric,
            "rows_read": processed,
            "ips": len(data),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en metric stats by IP: {str(e)}")
    finally:
        conn.close()

# --------------------- 2) Summary global (genérico) ---------------------
@router.get("/get_metric_stats_summary", summary="Resumen global (SNR_H / SNR_V / RX) filtrando PMP-SM")
def get_metric_stats_summary(
    column: str = Query(..., description="Columna origen: 'snr' o 'link_radio'"),
    metric: str = Query(..., description="Métrica: 'H', 'V' o 'rx'"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit_rows: int = Query(200000, ge=1, le=1000000)
):
    """
    Igual que el anterior pero acumula global (no por IP).
    SOLO números fijos; ignora listas/nulls/etc. Filtra i.tipo='PMP-SM'.
    """
    column = column.strip().lower()
    metric = metric.strip()

    if column not in ("snr", "link_radio"):
        raise HTTPException(status_code=400, detail="column debe ser 'snr' o 'link_radio'")
    if metric.lower() not in ("h", "v", "rx"):
        raise HTTPException(status_code=400, detail="metric debe ser 'H', 'V' o 'rx'")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        q = f"""
            SELECT c.ip, c.fecha, c.{column}
            FROM cambium_data c
            LEFT JOIN inventario i ON c.ip = i.ip
            WHERE i.tipo = 'PMP-SM'
        """
        params: List[Any] = []
        if start_date:
            q += " AND c.fecha >= %s"; params.append(start_date)
        if end_date:
            q += " AND c.fecha <= %s"; params.append(end_date)
        q += " ORDER BY c.fecha DESC LIMIT %s"; params.append(limit_rows)

        cursor.execute(q, params)

        total_ips_set = set()
        cnt = 0
        smin = None
        smax = None
        ssum = 0.0

        for ip, fecha, raw in cursor.fetchall():
            val = _extract_metric_fixed(raw, metric)
            if val is None:
                continue
            cnt += 1
            total_ips_set.add(ip)
            f = float(val)
            ssum += f
            smin = f if smin is None else min(smin, f)
            smax = f if smax is None else max(smax, f)

        avg = (ssum / cnt) if cnt > 0 else None
        return {
            "column": column,
            "metric": metric,
            "total_ips": len(total_ips_set),
            "total_mediciones": cnt,
            "promedio_general": None if avg is None else round(avg, 3),
            "max_global": None if smax is None else round(smax, 3),
            "min_global": None if smin is None else round(smin, 3),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en metric summary: {str(e)}")
    finally:
        conn.close()
