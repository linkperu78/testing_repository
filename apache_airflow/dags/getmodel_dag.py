from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'smartlink',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id="getmodel_dag",
    default_args=default_args,
    schedule_interval="0 0 * * *",  # Todos los dias a las 00:00
    catchup=False,
    tags=["modelos"]
) as dag:

    crear_modelos = BashOperator(
        task_id="crear_modelos_cambium",
        bash_command="""
        bash /home/support/docker_ia/smartlink_ia/forecast_neuralprophet/crear_modelos_cambium.sh
        """
    )

