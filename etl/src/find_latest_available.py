import json
from datetime import date
from pathlib import Path

import requests


BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

MAX_MONTHS_TO_CHECK = 12


def previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12

    return year, month - 1


def find_latest_available(start_year: int, start_month: int) -> tuple[int, int]:
    year = start_year
    month = start_month

    for _ in range(MAX_MONTHS_TO_CHECK):
        filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
        url = f"{BASE_URL}/{filename}"

        print(f"Checking {filename}...")

        response = requests.head(url, timeout=30)

        if response.status_code == 200:
            print(f"Found available data: {filename}")
            return year, month

        if response.status_code == 403:
            print(f"Not available: {filename}")
        else:
            response.raise_for_status()

        year, month = previous_month(year, month)

    raise RuntimeError(
        f"No available TLC data found in the last {MAX_MONTHS_TO_CHECK} months."
    )


if __name__ == "__main__":
    today = date.today()

    year, month = find_latest_available(
        today.year,
        today.month,
    )

    result = {
        "year": year,
        "month": month,
    }

    xcom_path = Path("/airflow/xcom/return.json")
    xcom_path.parent.mkdir(parents=True, exist_ok=True)
    xcom_path.write_text(json.dumps(result))

    print(f"Latest available data: {year}-{month:02d}")