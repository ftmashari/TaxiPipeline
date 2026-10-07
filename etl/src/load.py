import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


BASE_DIR = Path(__file__).resolve().parents[2]


ANALYTICS_DIR = (
    BASE_DIR
    / "data"
    / "analytics"
    / "yellow"
)

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def create_tables(engine) -> None:
    with engine.begin() as connection:

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS taxi_monthly_metrics (
                    source_month DATE NOT NULL,
                    pickup_date DATE NOT NULL,
                    trips INTEGER NOT NULL,
                    distance_sum DOUBLE PRECISION NOT NULL,
                    fare_sum DOUBLE PRECISION NOT NULL,
                    duration_sum DOUBLE PRECISION NOT NULL,
                    total_revenue DOUBLE PRECISION NOT NULL,
                    PRIMARY KEY (source_month, pickup_date)
                )
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS daily_taxi_metrics (
                    pickup_date DATE PRIMARY KEY,
                    trips INTEGER NOT NULL,
                    distance_sum DOUBLE PRECISION NOT NULL,
                    fare_sum DOUBLE PRECISION NOT NULL,
                    duration_sum DOUBLE PRECISION NOT NULL,
                    total_revenue DOUBLE PRECISION NOT NULL,
                    avg_distance DOUBLE PRECISION NOT NULL,
                    avg_fare DOUBLE PRECISION NOT NULL,
                    avg_duration DOUBLE PRECISION NOT NULL
                )
                """
            )
        )

    print("Tables are ready.")


def run(year: int, month: int) -> None:
    filename = f"daily_metrics_{year}-{month:02d}.parquet"
    input_file = ANALYTICS_DIR / filename

    if not input_file.exists():
        print(
            f"Analytics file does not exist: "
            f"{filename}. Nothing to load."
        )
        return

    print(f"Loading {filename}")

    df = pd.read_parquet(input_file)

    if df.empty:
        print("Analytics file is empty. Nothing to load.")
        return

    required_columns = {
        "source_month",
        "pickup_date",
        "trips",
        "distance_sum",
        "fare_sum",
        "duration_sum",
        "total_revenue",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # Make sure source_month represents exactly one source file.
    source_months = df["source_month"].unique()

    if len(source_months) != 1:
        raise ValueError(
            "Analytics file must contain exactly one source_month."
        )

    source_month = pd.Timestamp(source_months[0]).date()

    affected_dates = df["pickup_date"].tolist()

    engine = create_engine(DATABASE_URL)

    create_tables(engine)

    with engine.begin() as connection:

        # ---------------------------------------------------------
        # 1. Remove the previous contribution from this source file.
        # ---------------------------------------------------------
        connection.execute(
            text(
                """
                DELETE FROM taxi_monthly_metrics
                WHERE source_month = :source_month
                """
            ),
            {
                "source_month": source_month,
            },
        )

        # ---------------------------------------------------------
        # 2. Insert the current contribution.
        # ---------------------------------------------------------
        records = df[
            [
                "source_month",
                "pickup_date",
                "trips",
                "distance_sum",
                "fare_sum",
                "duration_sum",
                "total_revenue",
            ]
        ].to_dict(orient="records")

        connection.execute(
            text(
                """
                INSERT INTO taxi_monthly_metrics (
                    source_month,
                    pickup_date,
                    trips,
                    distance_sum,
                    fare_sum,
                    duration_sum,
                    total_revenue
                )
                VALUES (
                    :source_month,
                    :pickup_date,
                    :trips,
                    :distance_sum,
                    :fare_sum,
                    :duration_sum,
                    :total_revenue
                )
                """
            ),
            records,
        )

        # ---------------------------------------------------------
        # 3. Remove the affected dates from the final table.
        # ---------------------------------------------------------
        connection.execute(
            text(
                """
                DELETE FROM daily_taxi_metrics
                WHERE pickup_date = ANY(:affected_dates)
                """
            ),
            {
                "affected_dates": affected_dates,
            },
        )

        # ---------------------------------------------------------
        # 4. Recalculate affected dates from all source months.
        # ---------------------------------------------------------
        connection.execute(
            text(
                """
                INSERT INTO daily_taxi_metrics (
                    pickup_date,
                    trips,
                    distance_sum,
                    fare_sum,
                    duration_sum,
                    total_revenue,
                    avg_distance,
                    avg_fare,
                    avg_duration
                )
                SELECT
                    pickup_date,

                    SUM(trips) AS trips,

                    SUM(distance_sum) AS distance_sum,

                    SUM(fare_sum) AS fare_sum,

                    SUM(duration_sum) AS duration_sum,

                    SUM(total_revenue) AS total_revenue,

                    SUM(distance_sum)
                        / SUM(trips) AS avg_distance,

                    SUM(fare_sum)
                        / SUM(trips) AS avg_fare,

                    SUM(duration_sum)
                        / SUM(trips) AS avg_duration

                FROM taxi_monthly_metrics

                WHERE pickup_date = ANY(:affected_dates)

                GROUP BY pickup_date
                """
            ),
            {
                "affected_dates": affected_dates,
            },
        )

    print(
        f"Loaded {len(df):,} daily records "
        f"from source month {source_month}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--year",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--month",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    run(args.year, args.month)