from fastapi import APIRouter, Request, HTTPException, Depends
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
import json

from routes.__utils__ import insert_data, fetch_data
from models.rol_models import Rol

router = APIRouter()

@router.post("/add")
async def add_rol(rol: Rol, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "lista_rol", rol)
    
@router.get("/get")
async def get_roles(conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return fetch_data(conn, "lista_rol")