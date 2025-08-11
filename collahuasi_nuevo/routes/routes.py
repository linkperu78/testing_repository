from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError

import json

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Bienvenido a la API de Gestión de Base de Datos con FastAPI"}

@router.get("/hello_world")
def hello_world():
    return {"message": "Hello, world!"}

# Ruta síncrona
@router.get("/sync-route")
def sync_route():
    return {"message": "This is a sync route!"}

# Ruta asíncrona
@router.get("/async-route")
async def async_route():
    return {"message": "This is an async route!"}


