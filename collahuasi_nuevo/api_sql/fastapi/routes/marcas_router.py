from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
import json

from routes.__utils__ import insert_data, fetch_data
from models.marcas_models import Marca

router = APIRouter()

@router.post("/add")
def add_marca(marca: Marca):
    return insert_data("lista_marcas", marca)
    
@router.get("/get")
def get_marcas():
    return fetch_data("lista_marcas")
