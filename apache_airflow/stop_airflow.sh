#!/bin/bash

echo "Deteniendo Airflow..."

# Detener el webserver
if pgrep -f "airflow webserver" > /dev/null; then
    echo "Deteniendo webserver..."
    pkill -f "airflow webserver"
else
    echo "Webserver no está en ejecución."
fi

# Detener el scheduler
if pgrep -f "airflow scheduler" > /dev/null; then
    echo "Deteniendo scheduler..."
    pkill -f "airflow scheduler"
else
    echo "Scheduler no está en ejecución."
fi

echo "Airflow detenido correctamente."
