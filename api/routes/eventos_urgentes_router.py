from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timedelta
from connection import get_db_connection
from typing import Optional
from mariadb import IntegrityError
import json

router = APIRouter()

# TO DO: Implementar la función 'get_eventos_urgentes' que recibe un Request y devuelve un JSON con los eventos urgentes