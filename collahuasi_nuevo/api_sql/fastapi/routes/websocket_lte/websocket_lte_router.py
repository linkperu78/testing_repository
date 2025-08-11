# router/websocket_lte/websocket_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from routes.websocket_lte.LTE_utils import obtener_ips, hacer_peticion
from connection import get_db_connection

router = APIRouter()

@router.websocket("/lte")
async def websocket_lte(websocket: WebSocket):
    await websocket.accept()  # Acepta la conexión WebSocket
    try:
        while True:
            # Obtener la lista de IPs de la base de datos
            lista_ips = await obtener_ips()

            # Crear y ejecutar las tareas para hacer las peticiones a las IPs
            for ip in lista_ips:
                # Llamada asincrónica para hacer la petición
                tarea = await asyncio.create_task(hacer_peticion_y_enviar(ip, websocket))

            await asyncio.sleep(1)  # Espera antes de la siguiente ronda de peticiones

    except WebSocketDisconnect:
        print("Cliente desconectado, cerrando WebSocket.")
    except Exception as e:
        print(f"Error inesperado: {e}")

# Función de petición a la IP y envío inmediato de datos
async def hacer_peticion_y_enviar(ip, websocket: WebSocket):
    try:
        # Obtener los datos de la IP
        valor_json_ip = await hacer_peticion(ip)

        # Enviar los resultados al WebSocket tan pronto como estén listos
        if valor_json_ip:
            await websocket.send_json(valor_json_ip)
    except Exception as e:
        print(f"Error al procesar IP {ip}: {e}")
