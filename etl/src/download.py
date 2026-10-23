from pathlib import Path

import requests
import argparse


BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

RAW_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "yellow"
)


def download_month(year: int, month: int) -> Path | None:
    """
    Downloads the source file for the given year and month if it is available.
    Args:
        year (int): The year of the source file to download.
        month (int): The month of the source file to download (1-12).
    Returns:
        Path | None: The path to the downloaded file if successful, or None if the file is not available or already exists.
    """

    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"{BASE_URL}/{filename}"

    output_path = RAW_DIR / filename

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"Already exists: {filename}")
        return output_path

    print(f"Checking for {filename}...")

    response = requests.get(url, timeout=60)

    if response.status_code == 403:
        print(f"No update available: {filename}")
        return None

    response.raise_for_status()

    output_path.write_bytes(response.content)

    print(f"Downloaded: {output_path}")

    return output_path


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
    
    download_month(args.year, args.month)
