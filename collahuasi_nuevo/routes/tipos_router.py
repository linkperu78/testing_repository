from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
import json

from routes.__utils__ import insert_data, fetch_data
from models.tipos_models import Tipo


router = APIRouter()

@router.post("/add")
def add_tipo(tipo: Tipo):
    return insert_data("lista_tipo", tipo)
        
    
@router.get("/get")
def get_tipos():
    return fetch_data("lista_tipo")