from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import (
    KubernetesPodOperator,
)
from kubernetes.client import models as k8s


NAMESPACE = "default"
IMAGE = "ftmashari/taxipipeline-etl:latest"


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
        namespace=NAMESPACE,
        image=IMAGE,

        cmds=["python", "etl/src/find_latest_available.py"],

        do_xcom_push=True,

        get_logs=True,
        on_finish_action="delete_pod",
        config_file="~/.kube/config",
    )

    download = KubernetesPodOperator(
        task_id="download",
        name="taxi-download",
        namespace=NAMESPACE,

        image=IMAGE,

        cmds=[
            "python",
            "etl/src/download.py",
        ],

        arguments=[
            "--year",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['year'] }}",
            "--month",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['month'] }}",
        ],

        volumes=[
            k8s.V1Volume(
                name="etl-data",
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name="etl-data"
                ),
            ),
        ],

        volume_mounts=[
            k8s.V1VolumeMount(
                name="etl-data",
                mount_path="/app/data",
            ),
        ],

        is_delete_operator_pod=True,
        get_logs=True,
        config_file="~/.kube/config",
    )

    transform = KubernetesPodOperator(
        task_id="transform",
        name="taxi-transform",
        namespace=NAMESPACE,

        image=IMAGE,

        cmds=[
            "python",
            "etl/src/transform.py",
        ],

        arguments=[
            "--year",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['year'] }}",
            "--month",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['month'] }}",
        ],

        volumes=[
            k8s.V1Volume(
                name="etl-data",
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name="etl-data"
                ),
            ),
        ],

        volume_mounts=[
            k8s.V1VolumeMount(
                name="etl-data",
                mount_path="/app/data",
            ),
        ],

        is_delete_operator_pod=True,
        get_logs=True,
        config_file="~/.kube/config",
    )

    analytics = KubernetesPodOperator(
        task_id="analytics",
        name="taxi-analytics",
        namespace=NAMESPACE,

        image=IMAGE,
        image_pull_policy="Never",

        cmds=[
            "python",
            "etl/src/analytics.py",
        ],

        arguments=[
            "--year",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['year'] }}",
            "--month",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['month'] }}",
        ],

        volumes=[
            k8s.V1Volume(
                name="etl-data",
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name="etl-data"
                ),
            ),
        ],

        volume_mounts=[
            k8s.V1VolumeMount(
                name="etl-data",
                mount_path="/app/data",
            ),
        ],

        is_delete_operator_pod=True,
        get_logs=True,
        config_file="~/.kube/config",
    )

    load = KubernetesPodOperator(
        task_id="load",
        name="taxi-load",
        namespace=NAMESPACE,

        image=IMAGE,

        cmds=[
            "python",
            "etl/src/load.py",
        ],

        arguments=[
            "--year",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['year'] }}",
            "--month",
            "{{ ti.xcom_pull(task_ids='find_latest_available')['month'] }}",
        ],

        env_vars=[
            k8s.V1EnvVar(
                name=key,
                value_from=k8s.V1EnvVarSource(
                    secret_key_ref=k8s.V1SecretKeySelector(
                        name="postgres-secret",
                        key=key,
                    )
                ),
            )
            for key in (
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
                "POSTGRES_DB",
                "POSTGRES_HOST",
                "POSTGRES_PORT",
            )
        ],

        volumes=[
            k8s.V1Volume(
                name="etl-data",
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name="etl-data"
                ),
            ),
        ],

        volume_mounts=[
            k8s.V1VolumeMount(
                name="etl-data",
                mount_path="/app/data",
            ),
        ],

        is_delete_operator_pod=True,
        get_logs=True,
        config_file="~/.kube/config",
    )

    find_latest_available >> download >> transform >> analytics >> load