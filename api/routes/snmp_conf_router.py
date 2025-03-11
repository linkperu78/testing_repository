from fastapi import APIRouter, Query, HTTPException, Depends
from connection import get_db_connection
from typing import Optional, List
import json

from routes.__utils__ import insert_data, fetch_data
from models.snmp_conf_models import SnmpConf

router = APIRouter()

@router.post("/add")
async def add_snmp_conf(snmp_conf: SnmpConf, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "snmp_conf", snmp_conf)

@router.get("/get")
async def get_snmp_conf(conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return fetch_data(conn, "snmp_conf")

@router.get("/get_list_id")
async def get_snmp_conf_by_ids(
    index: List[int] = Query(..., description="Lista de IDs para filtrar SNMP Config"),
    conn_dep=Depends(get_db_connection)
):
    """
    Recupera registros de la tabla `snmp_conf` según una lista de IDs proporcionada.

    Args:
        index (List[int]): Lista de IDs de la configuración SNMP a recuperar.

    Returns:
        List[Dict[str, Any]]: Lista de registros con los datos de `snmp_conf`.
    """
    async with conn_dep as conn:
        try:
            cursor = conn.cursor()

            # Construir la consulta SQL con marcadores de posición
            placeholders = ",".join(["?"] * len(index))
            query = f"SELECT * FROM snmp_conf WHERE id IN ({placeholders})"
            cursor.execute(query, index)
            
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = []

            for row in rows:
                row_dict = dict(zip(column_names, row))

                # Parsear el campo 'credenciales' si existe y es un string JSON
                if "credenciales" in row_dict and isinstance(row_dict["credenciales"], str):
                    try:
                        credentials = json.loads(row_dict["credenciales"].replace("'", '"'))
                        row_dict.pop("credenciales")  # Remover el campo original
                        row_dict.update(credentials)  # Fusionar JSON parseado
                    except json.JSONDecodeError:
                        pass  # Mantener el original si falla la conversión

                result.append(row_dict)

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
