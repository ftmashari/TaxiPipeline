from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

from pod_settings import (
    COMMANDS,
    COMMON_KPO_ARGS,
    ETL_VOLUME_CONFIG,
    POSTGRES_ENV_VARS,
    SHARED_ARGS,
)

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
        do_xcom_push=True,
        **COMMON_KPO_ARGS,
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

    find_latest_available >> download >> transform >> analytics >> load