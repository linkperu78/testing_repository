from fastapi import APIRouter, HTTPException, Depends
from connection import get_db_connection
from mariadb import IntegrityError
from routes.__utils__ import insert_data, fetch_data, fetch_data_with_filter
from models.usuario_models import Usuario

router = APIRouter()

@router.post("/add")
async def add_usuario(usuario: Usuario, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:  # 🔥 Usa `async with` para obtener la conexión real
        return insert_data(conn=conn, table="usuarios", model=usuario)

@router.get("/get")
async def get_usuarios(conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return fetch_data(conn=conn, table="usuarios")

@router.get("/get_user/{user}")
async def get_usuario_by_username(user: str, conn_dep=Depends(get_db_connection)):
    async with conn_dep as conn:
        return fetch_data_with_filter(conn=conn, table="usuarios", column="user", value=user, operator="=")
