from bcapi_utils                import getRajantData, _PASSWORDS, _ROLES

import argparse
import traceback
import os
import sys

# Constantes
DEFAULT_ROL     = "admin"
DEBUG_MODE      = False

# Obtener ruta del script
script_path     = os.path.abspath(__file__)
script_folder   = os.path.dirname(script_path)
script_name     = os.path.basename(script_path)

# Argument parser
parser = argparse.ArgumentParser(description="Obtiene y guarda datos Rajant.")
parser.add_argument("-t", "--target", required=True, help="Dirección IP del equipo Rajant")
parser.add_argument("-o", "--output", default=os.getcwd(), help="Carpeta donde guardar el archivo de salida")
args = parser.parse_args()

ip = args.target
output_dir = args.output

# Validación extra (por si acaso)
if not ip:
    print("[ERROR] Debes especificar una IP con -t o --target")
    parser.print_help()
    sys.exit(1)

# Verificar que el directorio de salida exista
os.makedirs(output_dir, exist_ok=True)

# Ruta del archivo de salida
output_file = os.path.join(output_dir, f"{ip}_proto.txt")

# Programa principal
try:
    data_rajant = getRajantData(
        ipv4=ip,
        user=_ROLES[DEFAULT_ROL],
        passw=_PASSWORDS[DEFAULT_ROL],
        timeout=5,
        debug_mode=DEBUG_MODE
    )

    if data_rajant is None:
        print(f"No hay data para mostrar de {ip}")
        raise Exception("Respuesta vacía")

    # Mostrar en consola si está en modo debug
    if DEBUG_MODE:
        print(data_rajant)

    # Guardar en archivo
    with open(output_file, "w") as f:
        f.write(str(data_rajant))

    print(f"Datos guardados en: {output_file}")

except Exception as e:
    if str(e):
        print(f" !! {script_folder} main function error: {e}")
    if DEBUG_MODE:
        print(" > Error Details:")
        print(traceback.format_exc())
