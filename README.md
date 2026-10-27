# TaxiPipeline

A lightweight ETL pipeline for NYC Yellow Taxi trip data, orchestrated with Apache Airflow and executed as Kubernetes pods. The workflow checks for the latest available source month, downloads the Parquet file, transforms it, computes daily aggregates, and loads the results into PostgreSQL.

## Overview

This project demonstrates a practical data pipeline pattern:

- Airflow orchestrates the ETL stages
- each ETL step runs in its own Kubernetes pod
- data is persisted through a shared PVC mounted at `/app/data`
- PostgreSQL stores aggregated analytics and processing checkpoints
- source availability is checked against the official NYC TLC trip-data URLs
- GitHub Actions runs the test suite for pushes and pull requests targeting `main`, and publishes an updated ETL Docker image to Docker Hub when image-related files change on a push to `main`

## Architecture

The pipeline is organized as follows:

- `airflow/dags/taxi_pipeline.py` defines the DAG and task dependencies
- `airflow/dags/pod_settings.py` contains reusable Kubernetes pod configuration
- `etl/src/find_latest_available.py` checks which source month is latest and available
- `etl/src/download.py` downloads the matching Parquet file into the shared data volume
- `etl/src/transform.py` normalizes and prepares the raw data
- `etl/src/analytics.py` computes daily aggregations
- `etl/src/load.py` writes the analytics to PostgreSQL and records processed source months
- `k8s/` contains Kubernetes manifests for storage and the PostgreSQL database
- `.github/workflows/cicd.yml` runs the test suite on pushes and pull requests targeting `main`, and builds and publishes the ETL Docker image to Docker Hub on qualifying pushes to `main`


## Prerequisites

Before running the project, make sure you have:

- Python 3.13, matching the version used by CI and the Docker image
- Docker and Docker Compose for container-based use
- Kubernetes cluster access and `kubectl` only if deploying the Airflow tasks to Kubernetes
- `pytest` to run tests; install it with `pip install -r requirements-dev.txt`

## Environment variables

The ETL scripts read PostgreSQL connection values from environment variables:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

The local Postgres config is usually supplied through Docker Compose or a `.env` file.

## Running with Docker Compose

From the project root:

```bash
docker-compose up --build
```

This starts the services defined in `docker-compose.yaml`, including the application environment and the backing database if configured.

## Running Kubernetes

Apply the shared infrastructure manifests first:

```bash
kubectl apply -f k8s/etl-data-pvc.yaml
kubectl apply -f k8s/postgres.yaml
```

If you are using a Kubernetes Secret for PostgreSQL credentials, create it before the workload starts:

```bash
kubectl apply -f .secrets
```

If the secret is not yet created and you want to define it directly from environment values:

```bash
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=user \
  --from-literal=POSTGRES_PASSWORD=password \
  --from-literal=POSTGRES_DB=db \
  --from-literal=POSTGRES_HOST=host \
  --from-literal=POSTGRES_PORT=5432
```

This ensures the persistent volume claim, the Postgres service/deployment, and any required secret objects are in place before Airflow tasks run.

## Running Airflow locally

From the project root:

```bash
export AIRFLOW_HOME="$PWD/airflow"
source .venv/bin/activate
airflow standalone
```

## Airflow backfill

To backfill a specific month, trigger the `taxi_pipeline` DAG with the following configuration:

```json
{
  "backfill": true,
  "year": 2026,
  "month": 7
}
```

- `backfill`: Set to `true` to enable backfill mode.
- `year`: The year of the source data.
- `month`: The month of the source data (1–12).

Backfill mode reprocesses the specified month, replacing its existing contribution and recalculating affected daily aggregates without double-counting. For normal execution, trigger the DAG without configuration; it discovers the latest available month and skips it if already processed.

## Pipeline flow

1. `find_latest_available`
   - checks the latest available NYC taxi Parquet file at the TLC public URL
   - returns the newest month that exists and is not already processed
   - when backfill is enabled, selects the requested year and month and verifies that source data is available

2. `download`
   - downloads the selected month into the `etl-data` PVC mounted at `/app/data`

3. `transform`
   - cleans and reshapes the raw Parquet data into a format ready for analytics

4. `analytics`
   - computes daily KPI metrics such as trips, distance, fare, duration, and revenue

5. `load`
   - writes the monthly and daily metrics into PostgreSQL
   - updates the processed checkpoint table so duplicate loads are skipped

## Data model

The load step writes into these tables:

- `taxi_monthly_metrics`
- `daily_taxi_metrics`
- `processed_source_months`

The `processed_source_months` exists to avoid redownloading and reprocessing already-processed months.

## Tests

The test suite uses `pytest` and covers the ETL modules for downloading, transforming,
analytics, loading, and finding the latest available source month. The GitHub Actions
workflow runs the same suite using Python 3.13 on pushes to `main` and pull requests
targeting `main`.

Install the development dependencies from the project root:

```bash
pip install -r requirements-dev.txt
```

Run all tests with:

```bash
pytest
```

To run a specific test file, for example:

```bash
pytest -v etl/tests/test_transform.py
```

Pytest is configured in `pytest.ini` to find tests under `etl/tests` and import ETL
modules from `etl/src`.


## CI/CD pipeline

The GitHub Actions workflow is defined in `.github/workflows/cicd.yml`. For pushes to
`main` and pull requests targeting `main`, it checks out the repository, sets up
Python 3.13, installs the development dependencies, and runs `pytest`.

Docker image publishing runs only for pushes to `main` when image-related files have
changed: `Dockerfile`, `requirements.txt`, or files under `etl/src/`. The workflow logs
in to Docker Hub, builds the image, and pushes it as
`ftmashari/taxipipeline-etl:latest`. Configure the `DOCKERHUB_USERNAME` and
`DOCKERHUB_TOKEN` GitHub Actions secrets in the repository settings for this step to
succeed. Pull requests run tests but do not publish the image.

## Notes

- The workflow is intentionally built to be resilient to repeated runs.
- Data is kept in the shared persistent volume, which is reused across tasks.
- The `ON CONFLICT ... DO NOTHING` pattern prevents duplicate month markers when a source month is already marked as processed.

## To do
- Migrate to AWS
- Use Terraform for resources
