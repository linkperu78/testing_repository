from pydantic import BaseModel
from typing import Dict

class Servidor(BaseModel):
    ip          : str
    fecha       : str
    num_mv      : int
    info_mv     : Dict
    info_server : Dict
    info_snmp   : Dict