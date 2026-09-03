import argparse
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "yellow"
)

ANALYTICS_DIR = (
    BASE_DIR
    / "data"
    / "analytics"
    / "yellow"
)


def run(year: int, month: int) -> None:
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"

    input_file = PROCESSED_DIR / filename

    if not input_file.exists():
        print(
            f"Processed file does not exist: {filename}. "
            "Nothing to analyze."
        )
        return

    output_file = (
        ANALYTICS_DIR
        / f"daily_metrics_{year}-{month:02d}.parquet"
    )

    # Don't recalculate analytics if we've already done them
    if output_file.exists():
        print(
            f"Analytics already exist: "
            f"{output_file.name}. "
            "No update needed."
        )
        return

    print(f"Reading {input_file.name}")

    df = pd.read_parquet(input_file)

    daily_metrics = (
        df.groupby("pickup_date")
        .agg(
            trips=("pickup_date", "size"),
            avg_distance=("trip_distance", "mean"),
            avg_fare=("fare_amount", "mean"),
            avg_duration=("trip_duration_minutes", "mean"),
            total_revenue=("total_amount", "sum"),
        )
        .reset_index()
    )

    ANALYTICS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    run(
        year=args.year,
        month=args.month,
    )
