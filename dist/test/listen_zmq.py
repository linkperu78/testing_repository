import zmq

# === Conectarse al socket ZMQ del publicador ===
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")

# Suscribirse a todos los mensajes
socket.setsockopt_string(zmq.SUBSCRIBE, "")

print("📡 Escuchando datos del socket ZMQ en tcp://localhost:5555 ...\n")

try:
    while True:
        # Recibir y decodificar JSON
        data = socket.recv_json()
        print("Mensaje recibido:", data)
except KeyboardInterrupt:
    print("\nDetenido por el usuario")
finally:
    socket.close()
    context.term()
