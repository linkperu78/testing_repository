from fastapi import APIRouter
import platform
import os
import multiprocessing
import fastapi
import uvicorn
from typing import Dict


router = APIRouter()

@router.get("/info", summary="Información sobre el entorno de ejecución de la API")
def get_api_info() -> Dict:
    """
    Devuelve información útil del entorno donde está corriendo la API.
    """
    return {
        "python_version": platform.python_version(),
        "fastapi_version": fastapi.__version__,
        "uvicorn_version": uvicorn.__version__,
        "cpu_count": multiprocessing.cpu_count(),
        "worker_count_env": os.environ.get("WORKERS", "no definido"),
        "hostname": platform.node(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "pid": os.getpid(),
        "timezone": os.environ.get("TZ", "no definido")
    }
