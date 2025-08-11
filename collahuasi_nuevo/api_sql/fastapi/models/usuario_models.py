from pydantic import BaseModel
from typing import Dict

class Usuario(BaseModel):
    user: str
    psswrd: str
    email: str
    rol: str
