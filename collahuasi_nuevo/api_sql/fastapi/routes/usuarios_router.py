from fastapi import APIRouter, HTTPException
from connection import get_db_connection
from mariadb import IntegrityError

router = APIRouter()

from routes.__utils__ import insert_data, fetch_data, fetch_data_with_filter
from models.usuario_models import Usuario

@router.post("/add")
def add_usuario(usuario: Usuario):
    return insert_data("usuarios", usuario)
    
@router.get("/get")
def get_usuarios():
    return fetch_data("usuarios")

@router.get("/get_user/{user}")
def get_usuario_by_username(user: str):
    return fetch_data_with_filter("usuarios", "user", user, "=")