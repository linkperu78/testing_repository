from smartlink.http_utils import DB_API_URL
from LTE_module import USER_SSH_MIKROTIK, PASS_SSH_MIKROTIK, get_ip_lte_ssh
from time import time
import zmq
import requests
import asyncio
import os
import signal
import sys

# === Configuración inicial ===
TIPO = "LTE"
ESTADOS = {
    1: "OK",
    2: "TARDE",
    3: "DESCONECTADO"
}

# === TIEMPOS ===
INTERVALO_TIEMPO        = 5                         # Frecuencia de consulta
INTER_TIEMPO_ESTADO     = INTERVALO_TIEMPO * 2.5    # Límite para "TARDE"
MAX_TIEMPO_ESTADO       = INTERVALO_TIEMPO * 4      # Timeout de consulta
INTERVALO_INVENTARIO    = INTERVALO_TIEMPO * 3      # Frecuencia de actualización inventario

# === API - URLs ===
URL_API_INVENTARIO          = DB_API_URL + f"inventario/get/tipo/{TIPO}"
INVENTARIO_FALLBACK_PATH    = "/usr/smartlink/LTE/ips_inventario.txt"

# === ZeroMQ socket ===
context = zmq.Context()
zmq_socket = context.socket(zmq.PUB)
zmq_socket.bind("tcp://localhost:5555")

# === Estados globales ===
dict_ip_status      = {}
lista_ips_completa  = []
lista_ips_marca_anterior = []
procesos_en_curso   = {}

# === Obtener lista de IPs desde API o archivo local ===
def get_inventario_LTE():
    global lista_ips_completa
    try:
        response = requests.get(URL_API_INVENTARIO, timeout = INTERVALO_INVENTARIO - 3)
        if response.status_code == 200:
            data = response.json()
            lista_ips = [row["ip"] for row in data]
            # Guardar copia local
            with open(INVENTARIO_FALLBACK_PATH, "w") as f:
                f.write("\n".join(lista_ips))
            lista_ips_completa = lista_ips
            return lista_ips
    except Exception:
        pass

    if os.path.exists(INVENTARIO_FALLBACK_PATH):
        with open(INVENTARIO_FALLBACK_PATH, "r") as f:
            lista_ips = [line.strip() for line in f if line.strip()]
            lista_ips_completa = lista_ips
            return lista_ips
        
    return []


# === Hacer petición SSH con timeout y calcular estado ===
async def hacer_peticion_con_estado(ip):
    inicio = time()
    try:
        resultado = await asyncio.wait_for(
            asyncio.to_thread(get_ip_lte_ssh, 
                              ip_remote     = ip,
                              fullpath_script = "/usr/smartlink/LTE/ssh_LTE_request",
                              usuario       = USER_SSH_MIKROTIK,
                              contraseña    = PASS_SSH_MIKROTIK,
                              timeout_ssh   = MAX_TIEMPO_ESTADO - 1),
            timeout = MAX_TIEMPO_ESTADO
        )
    except asyncio.TimeoutError:
        resultado = None

    tiempo = time() - inicio

    if resultado:
        resultado["ip"] = ip
        if tiempo < INTER_TIEMPO_ESTADO:
            resultado["Estado IP"] = ESTADOS[1]
        else:
            resultado["Estado IP"] = ESTADOS[2]
    else:
        resultado = {"ip": ip,
                     "status" : "disconnected", 
                     "Estado IP": ESTADOS[3]}

    return resultado


# === Marca de tiempo ===
async def ciclo_marca():
    global lista_ips_marca_anterior, procesos_en_curso, dict_ip_status
    
    # Inicializar con todas las IPs del inventario
    lista_ips_marca_anterior = lista_ips_completa[:]
    
    while True:
        marca_inicio        = time()
        resultados_marca    = []
        nuevas_respuestas   = []

        # 1. Lanzar consultas para todas las IPs del ciclo actual
        for ip in lista_ips_marca_anterior:
            if ip not in procesos_en_curso:
                procesos_en_curso[ip] = asyncio.create_task(hacer_peticion_con_estado(ip))

        # 2. Esperar respuestas durante el intervalo
        tiempo_transcurrido = 0
        while tiempo_transcurrido < INTERVALO_TIEMPO - 0.5:     # Se le resta 0.5 segundos para darle una 
                                                                # ventana de tiempo para recibir correctamente las peticiones
            await asyncio.sleep(0.5)    # Revisar frecuentemente
            tiempo_transcurrido = time() - marca_inicio

            # Verificar tareas completadas
            tareas_completadas = [ip for ip, t in procesos_en_curso.items() 
                                if t.done()]
            
            for ip in tareas_completadas:
                tarea = procesos_en_curso[ip]
                try:
                    resultado = tarea.result()
                    resultados_marca.append(resultado)
                    nuevas_respuestas.append(ip)
                    dict_ip_status[ip] = resultado["Estado IP"]
                except Exception:
                    # Registrar falla pero no reintentar (se manejará en próximo ciclo)
                    dict_ip_status[ip] = ESTADOS[3]
                finally:
                    del procesos_en_curso[ip]  # Limpiar siempre

        # 3. Enviar resultados y preparar próximo ciclo
        for resultado in resultados_marca:
            zmq_socket.send_json(resultado)

        # 4. Solo las IPs que respondieron se consultarán en el próximo ciclo
        lista_ips_marca_anterior = nuevas_respuestas #if nuevas_respuestas else lista_ips_completa[:]
        
        # 5. Asegurar intervalo exacto
        tiempo_restante = INTERVALO_TIEMPO - (time() - marca_inicio)
        if tiempo_restante > 0:
            await asyncio.sleep(tiempo_restante)


# === Monitor de inventario ===
async def actualizar_inventario():
    inventario_prev = get_inventario_LTE()
    print(f"• Inventario obtenido = {inventario_prev}")

    await asyncio.sleep(INTERVALO_INVENTARIO)

    while True:
        start = time()
        nueva_lista = get_inventario_LTE()

        print(f"• Inventario obtenido = {nueva_lista}")

        if nueva_lista and nueva_lista != inventario_prev:
            print("\n⚠ Inventario cambiado, lanzando error...\n")
            raise ValueError("El inventario ha cambiado")           # Lanza error en lugar de reiniciar

        inventario_prev = nueva_lista
        delta = max(INTERVALO_INVENTARIO - (time() - start), 0)
        await asyncio.sleep(delta)


# === Mostrar estado ===
async def imprimir_estado():
    while True:
        print(f"\n→ Estado actual de IPs:")
        for ip, estado in dict_ip_status.items():
            print(f"{ip}: {estado}")
        await asyncio.sleep(INTERVALO_TIEMPO)


# === Manejador Ctrl + C ===
def signal_handler(sig, frame):
    print("\nTerminando ejecución...")
    for tarea in procesos_en_curso.values():
        tarea.cancel()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# === MAIN ===
async def main():
    await asyncio.gather(
        actualizar_inventario(),
        ciclo_marca(),
        #imprimir_estado()
    )

# -------------------------
if __name__ == "__main__":
    asyncio.run(main())
