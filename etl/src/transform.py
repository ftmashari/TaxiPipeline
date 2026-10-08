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


if __name__ == "__main__":
    import argparse

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

    filename = f"yellow_tripdata_{args.year}-{args.month:02d}.parquet"

    input_file = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "raw"
        / "yellow"
        / filename
    )

    output_file = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "processed"
        / "yellow"
        / filename
    )

    if output_file.exists():
        print(f"Already processed: {filename}")
    else:
        transform(input_file, output_file)