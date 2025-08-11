from pydantic import BaseModel

class Latencia(BaseModel):
    ip          : str
    latencia    : float
    fecha       : str
