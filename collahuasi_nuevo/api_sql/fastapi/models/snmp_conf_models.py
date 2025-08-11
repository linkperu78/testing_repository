from pydantic import BaseModel
from typing import Dict

class SnmpConf(BaseModel):
    comunidad: str
    version: int
    credenciales: Dict


