from pydantic import BaseModel
from typing import Dict

class CambiumData(BaseModel):
    ip: str
    fecha: str
    snr: Dict
    link_radio: Dict
    avg_power: Dict
    ifresults_metricas: Dict

