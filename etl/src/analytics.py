import argparse
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed" / "yellow"
ANALYTICS_DIR = BASE_DIR / "data" / "analytics" / "yellow"


def run(year: int, month: int) -> None:
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"

    input_file = PROCESSED_DIR / filename
    output_file = ANALYTICS_DIR / f"daily_metrics_{year}-{month:02d}.parquet"

    if not input_file.exists():
        print(
            f"Processed file does not exist: "
            f"{filename}. Nothing to analyze."
        )
        return

    if output_file.exists():
        print(
            f"Analytics already exist: "
            f"{output_file.name}. No update needed."
        )
        return

    print(f"Reading {input_file.name}")

    df = pd.read_parquet(input_file)

    if df.empty:
        print("Processed file is empty. Nothing to analyze.")
        return

    source_month = pd.Timestamp(
        year=year,
        month=month,
        day=1,
    ).date()

    daily_metrics = (
        df.groupby("pickup_date")
        .agg(
            trips=("pickup_date", "size"),
            distance_sum=("trip_distance", "sum"),
            fare_sum=("fare_amount", "sum"),
            duration_sum=("trip_duration_minutes", "sum"),
            total_revenue=("total_amount", "sum"),
        )
        .reset_index()
    )

    daily_metrics["source_month"] = source_month

    daily_metrics = daily_metrics[
        [
            "source_month",
            "pickup_date",
            "trips",
            "distance_sum",
            "fare_sum",
            "duration_sum",
            "total_revenue",
        ]
    ]

    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

    daily_metrics.to_parquet(
        output_file,
        index=False,
    )

    print(
        f"Created {output_file.name} "
        f"with {len(daily_metrics):,} rows"
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