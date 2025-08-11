from pydantic import BaseModel
from typing import Dict

class Sensor(BaseModel):
    __tablename__ = "sensores"
    fecha: str
    ip: str
    info: Dict
    valores: Dict

