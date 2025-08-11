# Guía completa de instalación y uso de Apache Airflow con MariaDB (con y sin internet)

## Requisitos previos

* Ubuntu 20.04 o superior
* Usuario con privilegios `sudo`
* Python 3.8 o superior
* `pip` y `virtualenv` instalados
* Acceso a MariaDB

---

## 1. Crear entorno de trabajo para Airflow

```bash
mkdir -p /home/support/apache_airflow
cd /home/support/apache_airflow
python3 -m venv .venv
source .venv/bin/activate
```

---

## 2. Instalar Airflow (con conexión a internet)

```bash
pip install --upgrade pip setuptools wheel
AIRFLOW_VERSION=2.8.1
PYTHON_VERSION=3.10
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

### Dependencias adicionales:

Crear archivo `requirements.txt`:

```txt
tzlocal
pymysql
```

Instalar:

```bash
pip install -r requirements.txt
```

---

## 3. Configurar MariaDB para Airflow

En el servidor MariaDB:

```sql
CREATE DATABASE airflow;
CREATE USER 'airflow'@'localhost' IDENTIFIED BY 'audio2023';
GRANT ALL PRIVILEGES ON airflow.* TO 'airflow'@'localhost';
FLUSH PRIVILEGES;
```

En el archivo `airflow.cfg`:

```ini
executor = LocalExecutor
sql_alchemy_conn = mysql+pymysql://airflow:audio2023@localhost/airflow
load_examples = False
```

---

## 4. Inicializar Airflow y crear usuario

```bash
export AIRFLOW_HOME=/home/support/apache_airflow
airflow db init

airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password audio2023
```

---

## 5. Instalar Airflow en entorno sin internet

En equipo con internet:

```bash
mkdir airflow_offline
cd airflow_offline
pip download "apache-airflow==2.8.1" --dest . --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.10.txt
```

Copiar carpeta `airflow_offline/` al equipo sin internet y luego:

```bash
cd /home/support/apache_airflow
source .venv/bin/activate
pip install --no-index --find-links=/ruta/a/airflow_offline apache-airflow
pip install --no-index --find-links=/ruta/a/airflow_offline -r requirements.txt
```

---

## 6. Scripts para iniciar y detener Airflow

### `start_airflow.sh`

```bash
#!/bin/bash
AIRFLOW_DIR="/home/support/apache_airflow"
VENV_DIR="$AIRFLOW_DIR/.venv"
source "$VENV_DIR/bin/activate"
export AIRFLOW_HOME="$AIRFLOW_DIR"
mkdir -p "$AIRFLOW_DIR/logs"

if ! pgrep -f "airflow scheduler" > /dev/null; then
    echo "Iniciando scheduler..."
    airflow scheduler > "$AIRFLOW_DIR/logs/scheduler.log" 2>&1 &
fi

if ! pgrep -f "airflow webserver" > /dev/null; then
    echo "Iniciando webserver en el puerto 8081..."
    airflow webserver --port 8081 > "$AIRFLOW_DIR/logs/webserver.log" 2>&1 &
fi

echo "Airflow iniciado."
```

### `stop_airflow.sh`

```bash
#!/bin/bash
echo "Deteniendo Airflow..."

if pgrep -f "airflow webserver" > /dev/null; then
    pkill -f "airflow webserver"
fi

if pgrep -f "airflow scheduler" > /dev/null; then
    pkill -f "airflow scheduler"
fi

echo "Airflow detenido."
```

Dar permisos:

```bash
chmod +x start_airflow.sh stop_airflow.sh
```

---

## 7. Crear servicio systemd para Airflow

Archivo: `/etc/systemd/system/airflow.service`

```ini
[Unit]
Description=Apache Airflow Daemon
After=network.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/home/ubuntu/apache_airflow/start_airflow.sh
ExecStop=/home/ubuntu/apache_airflow/stop_airflow.sh
Restart=always
Environment=AIRFLOW_HOME=/home/ubuntu/apache_airflow
WorkingDirectory=/home/ubuntu/apache_airflow

[Install]
WantedBy=multi-user.target
```

Habilitar y activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable airflow
sudo systemctl start airflow
```

**Nota:** si agregas/modificas DAGs:

```bash
sudo systemctl restart airflow
```

---

## 8. Crear un DAG de ejemplo

Archivo: `/home/support/apache_airflow/dags/ejemplo_dag.py`

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="ejemplo_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@hourly",
    catchup=False
) as dag:

    tarea = BashOperator(
        task_id="imprimir_hora",
        bash_command="date"
    )
```

Abrir en navegador:

```
http://<ip_del_servidor>:8081
```

---

## 9. Listo

Ya tienes Apache Airflow instalado y funcionando con MariaDB, en entornos con o sin internet, con scripts de inicio/parada y configurado como servicio. Puedes comenzar a desarrollar y automatizar tus DAGs con total control.
