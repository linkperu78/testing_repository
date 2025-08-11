from pydantic import BaseModel
from typing import Dict

class Predicciones(BaseModel):
    ip: str
    fecha: str
    fecha_prediccion: str
    tipo_prediccion: str
    value: float
    detalles: Dict
