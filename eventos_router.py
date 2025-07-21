from fastapi import APIRouter, HTTPException, Query, Path, Depends
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional, List
from routes.__utils__ import insert_data, insert_bulk_data, fetch_data_with_dates, fetch_data_with_filter_and_pagination
from models.eventos_models import Evento
from mariadb import IntegrityError
import json

router = APIRouter()

@router.post("/add", summary="Agregar un evento")
async def add_evento(evento: Evento):
    conn_dep = get_db_connection("smartlink")
    async with conn_dep as conn:
        return insert_data(conn=conn, table="eventos", model=evento)

@router.post("/add_list", summary="Agregar una lista de eventos")
async def add_evento_list(eventos: List[Evento]):
    conn_dep = get_db_connection("smartlink")
    async with conn_dep as conn:
        return insert_bulk_data(conn=conn, table="eventos", data=eventos, columns=Evento.model_fields.keys())

@router.get("/get", summary="Obtener eventos con filtro por fecha y paginación")
async def get_eventos(
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    conn_dep = get_db_connection("smartlink")
    async with conn_dep as conn:
        return fetch_data_with_dates(conn=conn, table="eventos", start_date=start_date, end_date=end_date, limit=limit, offset=offset, round_to_quarter_hour=False)

@router.get("/get_ip/{ip}", summary="Obtener eventos por IP con filtro de fecha y paginación")
async def get_eventos_by_ip(
    ip: str = Path(..., description="Dirección IP del evento"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    conn_dep = get_db_connection("smartlink")
    async with conn_dep as conn:
        return fetch_data_with_filter_and_pagination(conn=conn, table="eventos", ip_column="ip", ip=ip, start_date=start_date, end_date=end_date, limit=limit, offset=offset)


@router.get("/get_ip_codigo/{ip}/{codigo}", summary="Obtener eventos por ip y código con filtro de fecha y paginación")
async def get_eventos_by_ip_codigo(
    ip: str = Path(..., description="Dirección IP del evento"),
    codigo: str = Path(..., description="Código del evento"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
    offset: int = Query(0, description="Número de registros a omitir"),
    limit: int = Query(1000, description="Número de registros a mostrar"),
):
    conn_dep = get_db_connection("smartlink")
    async with conn_dep as conn:
        try:
            if not ip or not codigo:
                raise HTTPException(status_code=400, detail="IP y código son requeridos")
            cursor = conn.cursor()

            query = "SELECT * FROM eventos WHERE ip = %s AND codigo = %s"
            params = [ip, codigo]

            if start_date:
                query += " AND fecha >= %s"
                params.append(start_date)
            if end_date:
                query += " AND fecha <= %s"
                params.append(end_date)

            query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, tuple(params))
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(column_names, row)) for row in rows] if rows else []

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener los datos de la tabla eventos: {str(e)}")

@router.get("/get_recurrencia/{ip}/{codigo}", summary="Obtener valor de recurrencia de un evento por IP y código")
async def get_eventos_recurrencia(
    ip: str = Path(..., description="Dirección IP del evento"),
    codigo: str = Path(..., description="Código del evento"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio de la consulta"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin de la consulta"),
):
    conn_dep = get_db_connection("smartlink")
    async with conn_dep as conn:
        try:
            if not ip or not codigo:
                raise HTTPException(status_code=400, detail="IP y código son requeridos")
            cursor = conn.cursor()

            query = "SELECT recurrencia, fecha FROM eventos WHERE ip = %s AND codigo = %s"
            params = [ip, codigo]

            if start_date:
                query += " AND fecha >= %s"
                params.append(start_date)
            if end_date:
                query += " AND fecha <= %s"
                params.append(end_date)

            query += " ORDER BY fecha DESC LIMIT 1"

            cursor.execute(query, tuple(params))
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {"recurrencia": result[0], "fecha": result[1]}
            else:
                return {"recurrencia": 0, "fecha": None}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener el valor de recurrencia: {str(e)}")


@router.get("/urgentes")
async def get_eventos_urgentes(
    fecha: str = Query(None, description="Fecha de inicio en formato YYYY-MM-DD HH:MM:SS o YYYY-MM-DDTHH:MM:SS")
):
    conn_dep = get_db_connection("smartlink")
    async with conn_dep as conn:
        try:
            # 📌 Determinar fecha de consulta
            if fecha is None:
                fecha = (datetime.now() - timedelta(minutes=15, seconds=30)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                try:
                    fecha = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        fecha = datetime.strptime(fecha, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
                
                fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")

            print(f"🔍 Consultando eventos urgentes desde {fecha}")

            # 📌 Ejecutar consulta SQL
            cursor = conn.cursor(dictionary=True)  # Retornar resultados como diccionario
            cursor.execute("""
                SELECT e.ip, e.fecha, e.codigo, e.estado, e.problema, e.recurrencia, e.detalle, e.urgente, 
                       i.tag, i.marca, i.tipo
                FROM eventos e
                LEFT JOIN inventario i ON e.ip = i.ip
                WHERE e.urgente = 1 AND e.fecha > %s
            """, (fecha,))
            eventos = cursor.fetchall()
            cursor.close()

            print(f"📢 Se encontraron {len(eventos)} eventos urgentes.")

            if not eventos:
                return []

            # 📌 Procesar los eventos
            results = []
            for i in eventos:
                try:
                    detalle = json.loads(i["detalle"]) if isinstance(i["detalle"], str) else i["detalle"]
                except json.JSONDecodeError:
                    print(f"⚠️ Error decodificando JSON en detalle: {i['detalle']}")
                    detalle = {}  # Usar diccionario vacío si falla
                emoji = ""
                mensaje = None
                if i["estado"] == "Alarma":
                    emoji = "🔴"
                elif i["estado"] == "Alerta":
                    emoji = "🟡"
                if i["problema"].lower() == "señal deficiente":
                    mensaje = f"[{emoji} {str(i['fecha'])}] Equipo {i['tag']} ({i['marca']} - {i['tipo']}) presenta {i['problema']}. Última latencia: {detalle.get('latencia', 'N/A')}. Ocurrió {i['recurrencia']} veces en poco tiempo."
                elif i["problema"].lower() == "interferencia":
                    if "snr_h" in detalle.keys():
                        mensaje = f"[{emoji} {str(i['fecha'])}] Equipo {i['tag']} ({i['marca']} - {i['tipo']}) presenta {i['problema']}. Valor de SNR H: {detalle.get('snr_h', 'N/A')}. Ocurrió {i['recurrencia']} veces en poco tiempo."
                    elif "snr_v" in detalle.keys():
                        mensaje = f"[{emoji} {str(i['fecha'])}] Equipo {i['tag']} ({i['marca']} - {i['tipo']}) presenta {i['problema']}. Valor de SNR V: {detalle.get('snr_v', 'N/A')}. Ocurrió {i['recurrencia']} veces en poco tiempo."
                data = {
                    "ip": i["ip"],
                    "fecha": str(i["fecha"]),
                    "codigo": i["codigo"],
                    "estado": i["estado"],
                    "problema": i["problema"],
                    "recurrencia": i["recurrencia"],
                    "detalle": detalle,
                    "tag": i["tag"],
                    "marca": i["marca"],
                    "tipo": i["tipo"],
                    "emoji": emoji,
                    "mensaje": mensaje
                }
                results.append(data)
            print(f"📢 Mensajes generados: {results}")
            return results  # 📌 Ahora devuelve solo los mensajes

        except Exception as e:
            print(f"❌ Error en get_eventos_urgentes: {e}")
            raise HTTPException(status_code=500, detail=str(e))

