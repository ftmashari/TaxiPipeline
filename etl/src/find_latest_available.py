import json
import os
from datetime import date
from pathlib import Path

import requests
from sqlalchemy import create_engine, text

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

MAX_MONTHS_TO_CHECK = 12

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def previous_month(year: int, month: int) -> tuple[int, int]:
    """
    Returns the previous month and year as a tuple (year, month).
    If the current month is January, it returns December of the previous year.
    Args:
        year (int): The current year.
        month (int): The current month (1-12).
    Returns:
        tuple[int, int]: A tuple containing the previous year and month.
    """

    if month == 1:
        return year - 1, 12

    return year, month - 1


def is_available(year: int, month: int) -> bool:
    """
    Checks if the source file for the given year and month is available.
    Args:
        year (int): The year to check.
        month (int): The month to check (1-12).
    Returns:
        bool: True if the source file is available, False otherwise.
    """

    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"{BASE_URL}/{filename}"

    print(f"Checking source availability: {filename}")

    response = requests.head(
        url,
        timeout=30,
        allow_redirects=True,
    )

    if response.status_code == 200:
        return True

    if response.status_code in (403, 404):
        print(f"Source file is not available: {filename}")
        return False

    response.raise_for_status()
    return False


def is_processed(engine, year: int, month: int) -> bool:
    """
    Checks if the source month has already been processed.
    Args:
        engine: SQLAlchemy engine connected to the database.
        year (int): The year to check.
        month (int): The month to check (1-12).
    Returns:
        bool: True if the source month has been processed, False otherwise.
    """

    source_month = date(year, month, 1)
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM processed_source_months
                    WHERE source_month = :source_month
                )
            """),
            {"source_month": source_month},
        )
        return bool(result.scalar())


def find_work() -> dict:
    """
    Determines if there is new work to be done based on the availability of source files and whether they have already been processed.
    Returns:
        dict: A dictionary containing the result of the discovery process, including whether to process, the year and month to process, and the reason for the decision.
    """

    engine = create_engine(DATABASE_URL)

    try:
        # Ensure the checkpoint table exists, including on a fresh database.
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS processed_source_months (
                    source_month DATE PRIMARY KEY,
                    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """))

        today = date.today()
        year, month = today.year, today.month
        
        backfill = os.getenv("BACKFILL", "false").lower() == "true"

        if backfill:
            year = int(os.environ["BACKFILL_YEAR"])
            month = int(os.environ["BACKFILL_MONTH"])

            if not 1 <= month <= 12:
                raise ValueError(f"Invalid backfill month: {month}")

            if not is_available(year, month):
                raise ValueError(
                    f"Requested backfill source is unavailable: "
                    f"{year}-{month:02d}"
                )

            print(f"Backfill requested for {year}-{month:02d}")
            return {
                "process": True,
                "year": year,
                "month": month,
                "reason": "explicit_backfill",
            }

        for _ in range(MAX_MONTHS_TO_CHECK):
            if is_available(year, month):
                if is_processed(engine, year, month):
                    print(
                        f"{year}-{month:02d} is already processed. "
                        "No new work to do."
                    )
                    return {
                        "process": False,
                        "year": year,
                        "month": month,
                        "reason": "latest_available_month_already_processed",
                    }

                print(f"New source month found: {year}-{month:02d}")
                return {
                    "process": True,
                    "year": year,
                    "month": month,
                    "reason": "new_source_month",
                }

            year, month = previous_month(year, month)

        print("No source file found within the search window.")
        return {
            "process": False,
            "year": None,
            "month": None,
            "reason": "no_source_file_available",
        }

    finally:
        engine.dispose()


if __name__ == "__main__":
    result = find_work()
    xcom_path = Path("/airflow/xcom/return.json")
    xcom_path.parent.mkdir(parents=True, exist_ok=True)
    xcom_path.write_text(json.dumps(result))
    print(f"Discovery result: {result}")