from pathlib import Path

import pandas as pd


COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "fare_amount",
    "total_amount",
]


def transform(input_file: Path, output_file: Path) -> None:
    print(f"Processing {input_file.name}")

    df = pd.read_parquet(input_file)

    df = df[COLUMNS].copy()

    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"]
    )

    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"]
    )

    df["trip_duration_minutes"] = (
        df["tpep_dropoff_datetime"]
        - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    df["pickup_date"] = (
        df["tpep_pickup_datetime"].dt.date
    )

    # Basic data quality rules
    df = df[
        (df["passenger_count"] > 0)
        & (df["trip_distance"] > 0)
        & (df["fare_amount"] >= 0)
        & (df["total_amount"] >= 0)
        & (df["trip_duration_minutes"] > 0)
        & (df["trip_duration_minutes"] < 1440)
    ]

    df = df.dropna()

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        output_file,
        index=False,
    )

    print(
        f"Processed {len(df):,} rows → "
        f"{output_file.name}"
    )