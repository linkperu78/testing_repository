from pydantic import BaseModel
from typing import Dict

class Evento(BaseModel):
    ip: str
    fecha: str
    nodo: str
    estado: str
    problema: str
    recurrencia: int
    urgente: bool
    detalle: Dict


