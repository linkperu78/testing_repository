from pydantic import BaseModel
from typing import Dict

class rajant_performance(BaseModel):
    ip: str
    fecha: str
    server: str
    latencia: float
    bandwidth: Dict
    coreU: Dict

