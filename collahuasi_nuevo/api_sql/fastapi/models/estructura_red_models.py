from pydantic import BaseModel
from typing import Dict

class EstructuraRed(BaseModel):
    ip_fuente: str
    ip_cliente: str

