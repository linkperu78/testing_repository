from pydantic import BaseModel
from typing import Dict, Optional

class Inventario(BaseModel):
    ip          : str
    tag         : str
    marca       : str
    rol         : str
    tipo        : str
    snmp_conf   : int
    anotacion   : Optional[Dict] = None
    gps         : Optional[Dict] = None



