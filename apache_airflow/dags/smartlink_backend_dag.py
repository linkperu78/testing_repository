from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="smartlink_backend_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["smartlink"]
) as dag:

    tarea_latencia = BashOperator(
        task_id="latencia_factory",
        bash_command="python3 /home/support/factories/latencia_factory.py"
    )

    tarea_cambium = BashOperator(
        task_id="cambium_factory",
        bash_command="python3 /home/support/factories/cambium_data_factory.py"
    )

    tarea_mimosa = BashOperator(
        task_id="mimosa_factory",
        bash_command="python3 /home/support/factories/mimosa_data_factory.py"
    )

    tarea_rajant = BashOperator(
        task_id="rajant_factory",
        bash_command="python3 /home/support/factories/rajant_data_factory.py"
    )

    tarea_ubicacion_gps = BashOperator(
        task_id="ubicacion_gps_factory",
        bash_command="python3 /home/support/factories/ubicacion_gps_factory.py"
    )

    tarea_sensores = BashOperator(
        task_id="sensores_factory",
        bash_command="python3 /home/support/factories/sensores_data_factory.py"
    )

    tarea_predict = BashOperator(
        task_id="predecir_modelos_cambium",
        bash_command="""
	echo "Predecir modelos se hara proximamente"
	"""
    )

    # tarea_eventos = BashOperator(
    #     task_id="detectar_eventos",
    #     bash_command="""
    #     cd /home/support/docker_ia && \
    #     source .venv/bin/activate && \
    #     python3 -m smartlink_ia.eventos.main_eventos --insert
    #     """
    # )

    # tarea_eventos = BashOperator(
    #     task_id="detectar_eventos",
    #     bash_command="""
    #     docker run --rm \
    #     -v /etc/localtime:/etc/localtime:ro \
    #     ia_utils-lite smartlink_ia.eventos.main_eventos --insert
    #     """
    # )

    tarea_eventos = BashOperator(
        task_id="detectar_eventos",
        bash_command="""
        docker run --rm \
        -v /etc/localtime:/etc/localtime:ro \
        ia_utils-li smartlink_ia.eventos.main_eventos --insert
        """
    )

    tarea_mapeo_tareas = BashOperator(
        task_id="mapeo_tareas_gestor",
        bash_command="python3 /home/support/gestor_tareas/mapeo_tareas.py --insert"
    )


    # Dependencias
    tarea_cambium >> tarea_predict
    [tarea_latencia, tarea_cambium, tarea_mimosa, tarea_sensores] >> tarea_eventos
    tarea_eventos >> tarea_mapeo_tareas

