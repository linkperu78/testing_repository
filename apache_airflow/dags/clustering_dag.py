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

dag = DAG(
    'clustering_dag',
    default_args=default_args,
    description='DAG que ejecuta clustering a las 07:05 y 19:05 usando entorno virtual',
    schedule_interval='5 7,19 * * *',
    catchup=False,
    max_active_runs=1,
    tags=['clustering', 'smartlink'],
)

ejecutar_clustering = BashOperator(
    task_id='ejecutar_clustering',
    bash_command=(
        'cd /home/support/docker_ia && '
        'source .venv/bin/activate && '
        'python3 -m smartlink_ia.clustering.main_clustering --insert'
    ),
    dag=dag,
)
