import argparse
from pathlib import Path

from download import download_month
from transform import transform
from analytics import run as run_analytics
from load import run as run_load


BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed" / "yellow"


def run(year: int, month: int) -> None:
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    processed_file = PROCESSED_DIR / filename

    # 1. Download
    print("=" * 50)
    print("STEP 1: DOWNLOAD")
    print("=" * 50)

    input_file = download_month(year, month)

    if input_file is None:
        print(f"No update available for {year}-{month:02d}.")
        return

    # 2. Transform
    print("=" * 50)
    print("STEP 2: TRANSFORM")
    print("=" * 50)

    if processed_file.exists():
        print(f"Already processed: {filename}")
    else:
        transform(input_file, processed_file)

    # 3. Analytics
    print("=" * 50)
    print("STEP 3: ANALYTICS")
    print("=" * 50)

    run_analytics(year, month)

    # 4. Load
    print("=" * 50)
    print("STEP 4: LOAD")
    print("=" * 50)

    run_load(year, month)

    print("=" * 50)
    print(f"PIPELINE COMPLETE: {year}-{month:02d}")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run NYC Yellow Taxi ETL pipeline"
    )

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