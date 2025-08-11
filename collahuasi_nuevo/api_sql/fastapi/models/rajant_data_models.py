from pydantic import BaseModel
from typing import Dict

class RajantData(BaseModel):
    ip: str
    fecha: str
    config: Dict
    instamesh: Dict
    wired: Dict
    wireless: Dict


