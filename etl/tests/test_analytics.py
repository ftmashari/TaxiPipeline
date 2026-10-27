import pandas as pd
from unittest.mock import patch

import analytics

def test_run(tmp_path):
    dir = tmp_path / "data" / "processed" / "yellow"
    dir.mkdir(parents=True, exist_ok=True)
    input_file = dir / "yellow_tripdata_2026-10.parquet"
    output_file = tmp_path / "data" / "analytics" / "yellow" /"daily_metrics_2026-10.parquet"

    df = pd.DataFrame({
        "tpep_pickup_datetime": pd.to_datetime([
            "2026-10-22 10:00:00",
            "2026-10-22 11:00:00",
            "2026-10-23 12:00:00",
            "2026-10-23 13:00:00",
            "2026-10-25 14:00:00",
            "2026-10-25 15:00:00"
        ]),
        "tpep_dropoff_datetime": pd.to_datetime([
            "2026-10-22 10:30:00",
            "2026-10-22 11:30:00",
            "2026-10-23 12:30:00",
            "2026-10-23 13:30:00",
            "2026-10-25 14:30:00",
            "2026-10-25 15:30:00",
        ]),
        "passenger_count": [1, 2, 5, 3, 1, 2],
        "trip_distance": [5.0, 3.0, 2.0, 4.0, 1.0, 2.0],
        "fare_amount": [15.0, 5.0, 10.0, 20.0, 25.0, 30.0],
        "total_amount": [20.0, 15.0, 10.0, 25.0, 30.0, 5.0],
        "trip_duration_minutes": [30, 30, 30, 30, 30, 30],
        "pickup_date": pd.to_datetime([
            "2026-10-22",
            "2026-10-22",
            "2026-10-23",
            "2026-10-23",
            "2026-10-25",
            "2026-10-25"
        ])
    })

    df.to_parquet(input_file, index=False)

    # Change input_dir and output_dir in analytics.py to use tmp_path for testing then run analytics.run(year=2026, month=10)
    with patch('analytics.PROCESSED_DIR', tmp_path / "data" / "processed" / "yellow"), \
         patch('analytics.ANALYTICS_DIR', tmp_path / "data" / "analytics" / "yellow"):
        analytics.run(year=2026, month=10)

    # Read the output file and check the results
    result_df = pd.read_parquet(output_file)

    # Check that analytics were calculated correctly
    expected_df = pd.DataFrame({
        "source_month": [pd.Timestamp("2026-10-01").date()] * 3,
        "pickup_date": pd.to_datetime([
            "2026-10-22",
            "2026-10-23",
            "2026-10-25"
        ]),
        "trips": [2, 2, 2],
        "distance_sum": [8.0, 6.0, 3.0],
        "fare_sum": [20.0, 30.0, 55.0],
        "duration_sum": [60, 60, 60],
        "total_revenue": [35.0, 35.0, 35.0]
    })
    pd.testing.assert_frame_equal(result_df, expected_df)