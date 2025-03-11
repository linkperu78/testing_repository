from pydantic import BaseModel
from typing import Dict

class CambiumData(BaseModel):
    ip          : str
    fecha       : str
    snr         : Dict
    link_radio  : Dict
    avg_power   : Dict
    #snr_v: float
    #snr_h: float
    #link_radio_rx: float
    #link_radio_tx: float
    #avg_power_rx: float
    #avg_power_tx: float
    ifresults_metricas: Dict
    
