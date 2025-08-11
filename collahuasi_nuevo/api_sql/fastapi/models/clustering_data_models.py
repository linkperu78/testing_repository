from pydantic import BaseModel
from typing import Dict

class ClusteringData(BaseModel):
    ip: str
    fecha: str
    latitud: float
    longitud: float
    altitud: float
    latencia: float
    label: int
    cluster: int
