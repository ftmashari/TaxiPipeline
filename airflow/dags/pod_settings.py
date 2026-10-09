from kubernetes.client import models as k8s

NAMESPACE = "default"
IMAGE = "ftmashari/taxipipeline-etl:latest"

COMMON_KPO_ARGS = {
    "namespace": NAMESPACE,
    "image": IMAGE,
    "get_logs": True,
    "log_events_on_failure": True,
    "log_pod_spec_on_failure": True,
    "on_finish_action": "delete_succeeded_pod",
    "config_file": "~/.kube/config",
}

ETL_VOLUME_CONFIG = {
    "volumes": [
        k8s.V1Volume(
            name="etl-data",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                claim_name="etl-data"
            ),
        )
    ],
    "volume_mounts": [
        k8s.V1VolumeMount(
            name="etl-data",
            mount_path="/app/data",
        )
    ],
}

SHARED_ARGS = [
    "--year",
    "{{ ti.xcom_pull(task_ids='find_latest_available')['year'] }}",
    "--month",
    "{{ ti.xcom_pull(task_ids='find_latest_available')['month'] }}",
]

COMMANDS = {
    "find_latest_available": ["python", "etl/src/find_latest_available.py"],
    "download": ["python", "etl/src/download.py"],
    "transform": ["python", "etl/src/transform.py"],
    "analytics": ["python", "etl/src/analytics.py"],
    "load": ["python", "etl/src/load.py"],
}

POSTGRES_ENV_VARS = [
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
]

