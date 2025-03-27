import time
import subprocess
from datetime import datetime

def run_getmodels():
    print(f"[{datetime.now()}] Ejecutando getmodels...")
    subprocess.run(["python3", "-m", "IA.forecast_neuralprophet.getmodels"])

def run_predict():
    print(f"[{datetime.now()}] Ejecutando predict...")
    subprocess.run(["python3", "-m", "IA.forecast_neuralprophet.predict"])

def wait_until_next_interval(interval_minutes):
    now = datetime.now()
    seconds_now = now.minute * 60 + now.second
    interval_seconds = interval_minutes * 60
    seconds_to_wait = interval_seconds - (seconds_now % interval_seconds)
    if seconds_to_wait < 10:
        seconds_to_wait += interval_seconds
    print(f"Esperando {seconds_to_wait} segundos hasta el siguiente intervalo...")
    time.sleep(seconds_to_wait)

last_getmodels_day = None

while True:
    now = datetime.now()

    # Ejecutar getmodels a las 00:00:00 una vez por día
    if now.hour == 0 and now.minute == 0 and last_getmodels_day != now.date():
        run_getmodels()
        last_getmodels_day = now.date()

    # Ejecutar predict cada 15 minutos exactos
    run_predict()

    # Esperar hasta el siguiente cuarto de hora
    wait_until_next_interval(15)
