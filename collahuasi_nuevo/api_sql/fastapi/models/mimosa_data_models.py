from pydantic import BaseModel
from typing import Dict

class MimosaData(BaseModel):
    ip          : str
    fecha       : str
    interface   : Dict
    network     : Dict
