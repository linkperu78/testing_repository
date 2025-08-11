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
                              timeout_ssh   = MAX_TIEMPO_ESTADO + 1),
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
    lista_ips_marca_anterior = lista_ips_completa[:]
    
    while True:
        marca_inicio = time()

        # Lanzar consultas para las IPs de esta marca
        for ip in lista_ips_marca_anterior:
            if ip not in procesos_en_curso:
                #print(f" ○ ○ Creando consulta para {ip}")
                procesos_en_curso[ip] = asyncio.create_task(hacer_peticion_con_estado(ip))

        nuevas_respuestas   = []       # IPs que respondieron en esta marca
        resultados_marca    = []        # Resultados acumulados de esta marca
        tiempo_restante     = INTERVALO_TIEMPO
        
        marca_ips = lista_ips_marca_anterior[:]

        # Revisión estable cada 1 segundo
        while tiempo_restante > 0:
            await asyncio.sleep(min(1, tiempo_restante))

            # Revisar tareas terminadas
            tareas_en_curso = [procesos_en_curso[ip] for ip in marca_ips if ip in procesos_en_curso]
            done = [t for t in tareas_en_curso if t.done()]

            for tarea in done:
                try:
                    resultado = tarea.result()
                except Exception:
                    continue

                ip = resultado["ip"]
                dict_ip_status[ip] = resultado["Estado IP"]

                resultados_marca.append(resultado)  # Guardar resultado
                nuevas_respuestas.append(ip)        # Contar como respuesta
                del procesos_en_curso[ip]

            # Actualizar tiempo restante
            tiempo_restante = INTERVALO_TIEMPO - (time() - marca_inicio)

        # Enviar todos los resultados de la marca juntos
        for _result in resultados_marca:
            zmq_socket.send_json(_result)

        # Si nadie respondió, consultar todo el inventario la próxima vez
        lista_ips_marca_anterior = nuevas_respuestas


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
            print("\n⚠ Inventario cambiado, reiniciando proceso...\n")
            os.execv(sys.executable, [sys.executable] + sys.argv)

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


if __name__ == "__main__":
    asyncio.run(main())
