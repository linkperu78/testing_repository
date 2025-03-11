from fastapi import APIRouter, Depends
from routes.__utils__ import insert_data, fetch_data
from connection import get_db_connection
from models.tipos_models import Tipo


router = APIRouter()

@router.post("/add")
async def add_tipo(tipo: Tipo, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "lista_tipo", tipo)
    
@router.get("/get")
async def get_tipos(conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return fetch_data(conn, "lista_tipo")