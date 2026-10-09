from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.standard.operators.python import BranchPythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator

from pod_settings import (
    COMMANDS,
    COMMON_KPO_ARGS,
    ETL_VOLUME_CONFIG,
    POSTGRES_ENV_VARS,
    SHARED_ARGS,
)


def choose_pipeline_path(ti):
    result = ti.xcom_pull(task_ids="find_latest_available")

    if not result:
        raise ValueError("Discovery task returned no XCom result.")

    if result.get("process") is True:
        return "download"

    print(f"No new data to process: {result.get('reason')}")
    return "no_new_data"


with DAG(
    dag_id="taxi_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["taxi", "kubernetes", "etl"],
) as dag:

    find_latest_available = KubernetesPodOperator(
        task_id="find_latest_available",
        name="taxi-find-latest",
        cmds=COMMANDS["find_latest_available"],
        env_vars=POSTGRES_ENV_VARS,
        do_xcom_push=True,
        **COMMON_KPO_ARGS,
    )
    
    check_for_new_data = BranchPythonOperator(
        task_id="check_for_new_data",
        python_callable=choose_pipeline_path,
    )
    
    no_new_data = EmptyOperator(
        task_id="no_new_data",
    )

    download = KubernetesPodOperator(
        task_id="download",
        name="taxi-download",
        cmds=COMMANDS["download"],
        arguments=SHARED_ARGS,
        **COMMON_KPO_ARGS,
        **ETL_VOLUME_CONFIG,
    )

    transform = KubernetesPodOperator(
        task_id="transform",
        name="taxi-transform",
        cmds=COMMANDS["transform"],
        arguments=SHARED_ARGS,
        **COMMON_KPO_ARGS,
        **ETL_VOLUME_CONFIG,
    )

    analytics = KubernetesPodOperator(
        task_id="analytics",
        name="taxi-analytics",
        cmds=COMMANDS["analytics"],
        arguments=SHARED_ARGS,
        **COMMON_KPO_ARGS,
        **ETL_VOLUME_CONFIG,
    )

    load = KubernetesPodOperator(
        task_id="load",
        name="taxi-load",
        cmds=COMMANDS["load"],
        env_vars=POSTGRES_ENV_VARS,
        arguments=SHARED_ARGS,
        **COMMON_KPO_ARGS,
        **ETL_VOLUME_CONFIG,
    )

    find_latest_available >> check_for_new_data >> [download, no_new_data]
    download >> transform >> analytics >> load