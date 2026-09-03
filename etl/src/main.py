import argparse
from pathlib import Path

from download import download_month
from transform import transform


BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "yellow"
)


def run(year: int, month: int) -> None:
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"

    output_file = PROCESSED_DIR / filename

    # Already processed
    if output_file.exists():
        print(
            f"Already processed: {filename}. "
            "No update needed."
        )
        return

    print(f"New data detected: {filename}")

    input_file = download_month(year, month)

    # Data isn't available yet
    if input_file is None:
        print(
            f"No update available for "
            f"{year}-{month:02d}."
        )
        return

    transform(
        input_file,
        output_file,
    )

    print(
        f"Successfully processed "
        f"{year}-{month:02d}"
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