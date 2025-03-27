import time
import subprocess
from datetime import datetime, timedelta

GETMODELS_HORA = 0  # 00:00:00
PREDICT_INTERVAL = 15  # minutos

def run_getmodels():
    print(f"[{datetime.now()}] Ejecutando getmodels...")
    subprocess.run(["python3", "-m", "IA.forecast_neuralprophet.getmodels"])
    next_run = datetime.now().replace(hour=GETMODELS_HORA, minute=0, second=0, microsecond=0) + timedelta(days=1)
    print(f"[INFO] Próxima ejecución de getmodels: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

def run_predict():
    print(f"[{datetime.now()}] Ejecutando predict...")
    subprocess.run(["python3", "-m", "IA.forecast_neuralprophet.predict"])
    now = datetime.now()
    next_minute = ((now.minute // PREDICT_INTERVAL) + 1) * PREDICT_INTERVAL
    next_hour = now.hour + (next_minute // 60)
    next_minute = next_minute % 60
    next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=(next_hour - now.hour), minutes=next_minute)
    print(f"[INFO] Próxima ejecución de predict: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")

def wait_until_next_interval(interval_minutes):
    now = datetime.now()
    seconds_now = now.minute * 60 + now.second
    interval_seconds = interval_minutes * 60
    seconds_to_wait = interval_seconds - (seconds_now % interval_seconds)
    if seconds_to_wait < 10:
        seconds_to_wait += interval_seconds
    print(f"[WAIT] Esperando {seconds_to_wait} segundos hasta el siguiente cuarto de hora...")
    time.sleep(seconds_to_wait)

last_getmodels_day = None

while True:
    now = datetime.now()

    # Ejecutar getmodels a las 00:00:00 una vez por día
    if now.hour == GETMODELS_HORA and now.minute == 0 and last_getmodels_day != now.date():
        run_getmodels()
        last_getmodels_day = now.date()

    # Ejecutar predict cada 15 minutos exactos
    run_predict()

    # Esperar hasta el siguiente cuarto de hora
    wait_until_next_interval(PREDICT_INTERVAL)
