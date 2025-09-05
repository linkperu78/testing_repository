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

# --------------------- Helpers ---------------------
def _is_num(x: Any) -> bool:
    try:
        f = float(x)
        return not (math.isnan(f) or math.isinf(f))
    except Exception:
        return False

def _to_float_fixed(x: Any) -> Optional[float]:
    # Solo números "fijos": int/float o str-num. Strings JSON -> si decodifica a número, ok; si lista/dict -> None.
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x) if _is_num(x) else None
    if isinstance(x, str):
        xs = x.strip()
        if _is_num(xs):
            return float(xs)
        try:
            j = json.loads(xs)
        except Exception:
            return None
        return float(j) if _is_num(j) else None
    return None  # listas/dicts -> ignorar

def _extract_metric_fixed(raw: Any, key: str) -> Optional[float]:
    # Extrae 'H'/'V'/'rx' solo si termina en número fijo. Listas/dicts anidados -> ignorar.
    if isinstance(raw, str):
        s = raw.strip()
        try:
            raw = json.loads(s)
        except Exception:
            return _to_float_fixed(s)

    if isinstance(raw, dict):
        val = None
        if key in raw:
            val = raw[key]
        else:
            for k, v in raw.items():
                if str(k).lower() == key.lower():
                    val = v; break
        if val is None or isinstance(val, (list, dict)):
            return None
        return _to_float_fixed(val)

    if isinstance(raw, list):
        return None

    return _to_float_fixed(raw)

def _classify(metric: str, val: float) -> str:
    m = metric.lower()
    if m in ("h", "v"):
        if val > 20:
            return "optimo"
        if val >= 16 and val < 20:
            return "alerta"
        if val >= 0 and val < 16:
            return "alarma"
        return "alarma"  # negativos -> alarma
    elif m == "rx":
        if val >= -70 and val <= 0:
            return "optimo"
        if val >= -80 and val < -70:
            return "alerta"
        if val >= -90 and val < -80:
            return "alarma"
        return "alarma"  # < -90 peor que alarma estándar
    return "optimo"

def _safe_pct(malos: int, buenos: int) -> float:
    if buenos > 0:
        return round((malos / buenos) * 100.0, 2)
    return 100.0 if malos > 0 else 0.0

# --------------------- Endpoints ---------------------

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



# --------------------- 1) Stats por IP ---------------------
@router.get("/get_metric_stats_by_ip", summary="Estadísticas por IP (SNR_H / SNR_V / RX) filtrando PMP-SM")
def get_metric_stats_by_ip(
    column: str = Query(..., description="Columna: 'snr' o 'link_radio'"),
    metric: str = Query(..., description="Métrica: 'H', 'V' o 'rx'"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit_rows: int = Query(200000, ge=1, le=1000000, description="Filas a leer"),
    ip_filter: Optional[str] = Query(None, description="Filtrar por IP exacta (opcional)")
):
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
            SELECT c.ip, c.fecha, c.{column}, i.tag, i.marca, i.rol, i.tipo
            FROM cambium_data c
            LEFT JOIN inventario i ON c.ip = i.ip
            WHERE i.tipo = 'PMP-SM'
        """
        params: List[Any] = []
        if ip_filter:
            q += " AND c.ip = %s"; params.append(ip_filter)
        if start_date:
            q += " AND c.fecha >= %s"; params.append(start_date)
        if end_date:
            q += " AND c.fecha <= %s"; params.append(end_date)
        q += " ORDER BY c.fecha DESC LIMIT %s"; params.append(limit_rows)

        cursor.execute(q, params)

        stats: Dict[str, Dict[str, Any]] = {}
        inv: Dict[str, Dict[str, Any]] = {}
        processed = 0
        mkey = metric
        mkey_l = metric.lower()

        for ip, fecha, raw, tag, marca, rol, tipo in cursor.fetchall():
            # guarda inventario por IP (primer valor no nulo)
            inv.setdefault(ip, {"tag": tag, "marca": marca, "rol": rol, "tipo": tipo})

            val = _extract_metric_fixed(raw, mkey)
            if val is None:
                processed += 1
                continue

            cat = _classify(mkey, float(val))
            s = stats.setdefault(ip, {
                "total_mediciones": 0, "sum": 0.0, "min": None, "max": None,
                "alertas": 0, "alarmas": 0, "buenos": 0
            })

            s["total_mediciones"] += 1
            s["sum"] += float(val)
            s["min"] = float(val) if s["min"] is None else min(s["min"], float(val))
            s["max"] = float(val) if s["max"] is None else max(s["max"], float(val))
            if cat == "alerta":
                s["alertas"] += 1
            elif cat == "alarma":
                s["alarmas"] += 1
            else:
                s["buenos"] += 1

            processed += 1

        # armar salida
        out: List[Dict[str, Any]] = []
        for ip, s in stats.items():
            avg = (s["sum"] / s["total_mediciones"]) if s["total_mediciones"] > 0 else None
            malos = s["alertas"] + s["alarmas"]
            buenos = s["buenos"]
            pref = mkey_l  # 'h'/'v'/'rx'

            row = {
                "ip": ip,
                "tag": inv.get(ip, {}).get("tag"),
                "marca": inv.get(ip, {}).get("marca"),
                "rol": inv.get(ip, {}).get("rol"),
                "tipo": inv.get(ip, {}).get("tipo"),
                "total_mediciones": s["total_mediciones"],
                f"promedio_{pref}": None if avg is None else round(avg, 3),
                f"min_{pref}": None if s["min"] is None else round(s["min"], 3),
                f"max_{pref}": None if s["max"] is None else round(s["max"], 3),
                f"total_alertas_{pref}": s["alertas"],
                f"total_alarmas_{pref}": s["alarmas"],
                f"porcentaje_no_optimos_{pref}": _safe_pct(malos, buenos),
            }
            out.append(row)

        # ordenar por max desc
        out.sort(key=lambda d: (d.get(f"max_{mkey_l}") if d.get(f"max_{mkey_l}") is not None else -1e18), reverse=True)

        return {
            "column": column,
            "metric": metric,
            "rows_read": processed,
            "total_records": len(out),
            "data": out
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en metric stats by IP: {str(e)}")
    finally:
        conn.close()

# --------------------- 2) Summary global ---------------------
@router.get("/get_metric_stats_summary", summary="Resumen global (SNR_H / SNR_V / RX) filtrando PMP-SM")
def get_metric_stats_summary(
    column: str = Query(..., description="Columna: 'snr' o 'link_radio'"),
    metric: str = Query(..., description="Métrica: 'H', 'V' o 'rx'"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit_rows: int = Query(200000, ge=1, le=1000000)
):
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

        ips_set = set()
        cnt = 0
        ssum = 0.0
        smin = None
        smax = None
        alertas = 0
        alarmas = 0
        buenos = 0
        mkey_l = metric.lower()

        for ip, fecha, raw in cursor.fetchall():
            val = _extract_metric_fixed(raw, metric)
            if val is None:
                continue
            v = float(val)
            cat = _classify(metric, v)

            cnt += 1
            ips_set.add(ip)
            ssum += v
            smin = v if smin is None else min(smin, v)
            smax = v if smax is None else max(smax, v)
            if cat == "alerta":
                alertas += 1
            elif cat == "alarma":
                alarmas += 1
            else:
                buenos += 1

        avg = (ssum / cnt) if cnt > 0 else None
        malos = alertas + alarmas

        result = {
            "column": column,
            "metric": metric,
            "total_ips": len(ips_set),
            "total_mediciones": cnt,
            f"promedio_{mkey_l}": None if avg is None else round(avg, 3),
            f"max_{mkey_l}": None if smax is None else round(smax, 3),
            f"min_{mkey_l}": None if smin is None else round(smin, 3),
            f"total_alertas_{mkey_l}": alertas,
            f"total_alarmas_{mkey_l}": alarmas,
            f"porcentaje_no_optimos_{mkey_l}": _safe_pct(malos, buenos),
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en metric summary: {str(e)}")
    finally:
        conn.close()
