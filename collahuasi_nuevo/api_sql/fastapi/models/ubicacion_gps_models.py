from pydantic import BaseModel
from typing import Dict

class UbicacionGPS(BaseModel):
    ip: str
    fecha: str
    latitud: float
    longitud: float
    altitud: float


