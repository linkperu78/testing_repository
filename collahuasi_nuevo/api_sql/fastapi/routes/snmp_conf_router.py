from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
import json

from routes.__utils__ import insert_data, fetch_data
from models.snmp_conf_models import SnmpConf


router = APIRouter()

@router.post("/add")
def add_snmp_conf(snmp_conf: SnmpConf):
    return insert_data("snmp_conf", snmp_conf)

    
@router.get("/get")
def get_snmp_conf():
    return fetch_data("snmp_conf")


@router.get("/get_list_id")
def get_snmp_conf(index: list[int] = Query(...)):  # Accept multiple `index` values
    conn = get_db_connection()
    cursor = conn.cursor()

    # Convert list of indexes into a tuple for SQL query
    query = f"SELECT * FROM snmp_conf WHERE id IN ({','.join(['?']*len(index))})"
    cursor.execute(query, index)
    
    column_names = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        row_dict = dict(zip(column_names, row))

        # Parse 'credenciales' field if it exists
        if "credenciales" in row_dict and isinstance(row_dict["credenciales"], str):
            try:
                credentials = json.loads(row_dict["credenciales"].replace("'", '"'))
                row_dict.pop("credenciales")  # Remove original key
                row_dict.update(credentials)  # Merge parsed JSON
            except json.JSONDecodeError:
                pass  # Keep original if parsing fails

        result.append(row_dict)

    return result