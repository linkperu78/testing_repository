from fastapi import APIRouter, HTTPException, Depends
from connection import get_db_connection
from routes.__utils__ import insert_data, fetch_data
from models.marcas_models import Marca

router = APIRouter()

@router.post("/add")
async def add_marca(marca: Marca, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return insert_data(conn, "lista_marcas", marca)

@router.get("/get")
async def get_marcas(conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return fetch_data(conn, "lista_marcas")
