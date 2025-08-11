# routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from datetime import datetime

router = APIRouter()

@router.websocket("/time")
async def websocket_time(websocket: WebSocket):
    await websocket.accept()  # Acepta la conexión WebSocket
    try:
        while True:
            await websocket.send_json({"json1": "json1"})  # Enviar la hora al cliente
            await websocket.send_json({"json2": "json2"})  # Enviar la hora al cliente
            await websocket.send_json({"json3": "json3"})  # Enviar la hora al cliente
            await asyncio.sleep(5)  # Espera 5 segundos antes de enviar la siguiente hora
    except WebSocketDisconnect:
        print("Cliente desconectado, cerrando WebSocket.")
    except Exception as e:
        print(f"Error inesperado: {e}")