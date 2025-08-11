from pydantic import BaseModel
from typing import Dict, List

class LTE(BaseModel):
    ip          : str
    fecha       : str
    sistema     : Dict
    enlaces     : List[Dict[str, str]]
    estado      : Dict
    