#!/bin/bash

# Ruta del entorno de Airflow
AIRFLOW_DIR="/home/ubuntu/apache_airflow"
#AIRFLOW_DIR="/home/support/apache_airflow"
VENV_DIR="$AIRFLOW_DIR/.venv"

# Activar entorno virtual
source "$VENV_DIR/bin/activate"

# Exportar variable de entorno
export AIRFLOW_HOME="$AIRFLOW_DIR"

# Iniciar scheduler en background (si no está ya corriendo)
if ! pgrep -f "airflow scheduler" > /dev/null; then
    echo "Iniciando airflow scheduler..."
    airflow scheduler > "$AIRFLOW_DIR/logs/scheduler.log" 2>&1 &
else
    echo "Scheduler ya está en ejecución."
fi

# Iniciar webserver en background (si no está ya corriendo)
if ! pgrep -f "airflow webserver" > /dev/null; then
    echo "Iniciando airflow webserver en el puerto 8081..."
    airflow webserver --port 8081 > "$AIRFLOW_DIR/logs/webserver.log" 2>&1 &
else
    echo "Webserver ya está en ejecución."
fi

echo "Airflow iniciado correctamente."
