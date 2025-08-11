from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import PlainTextResponse, JSONResponse
import json
import os

router = APIRouter()

# Ruta donde se encuentran los archivos JSON
DATA_FOLDER = "/usr/smartlink/heatmap"  # Modifica esta ruta según corresponda

@router.get("/{marca}/{ip}", summary="Obtener datos específicos de una IP desde un archivo JSON")
async def get_marca_ip_data(
    marca: str = Path(..., description="Nombre de la marca"),
    ip: str = Path(..., description="Dirección IP a buscar")
):
    marca_match     = marca.upper()
    marca_folder    = os.path.join(DATA_FOLDER, marca_match)
    file_path       = os.path.join(marca_folder, f"{ip}.csv")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Archivo {marca_match}/{ip}.csv no encontrado")
    
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    return PlainTextResponse(content, media_type="text/plain")


@router.get("/{marca}", summary="Listar todos los archivos CSV de una marca")
async def list_marca_csv_files(
    marca: str = Path(..., description="Nombre de la marca")
):
    marca_match = marca.upper()
    marca_folder = os.path.join(DATA_FOLDER, marca_match)

    if not os.path.exists(marca_folder):
        raise HTTPException(status_code=404, detail=f"Carpeta de la marca {marca_match} no encontrada")

    # Listar todos los archivos .csv en la carpeta de la marca
    csv_files = [f for f in os.listdir(marca_folder) if f.endswith('.csv')]

    if not csv_files:
        raise HTTPException(status_code=404, detail=f"No se encontraron archivos CSV en la carpeta de la marca {marca_match}")

    # Devuelve solo la lista de archivos CSV
    return JSONResponse(content=csv_files)
