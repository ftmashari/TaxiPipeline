import pandas as pd
import transform

def test_transform(tmp_path):
    input_file = tmp_path / "input.parquet"
    output_file = tmp_path / "output.parquet"

    df = pd.DataFrame({
        "tpep_pickup_datetime": pd.to_datetime([
            "2026-10-22 10:00:00",
            "2026-10-22 11:00:00",
            "2026-10-22 12:00:00",
            "2026-10-22 13:00:00",
            "2026-10-22 14:00:00",
            "2026-10-22 15:00:00"
        ]),
        "tpep_dropoff_datetime": pd.to_datetime([
            "2026-10-22 10:30:00",
            "2026-10-22 11:30:00",
            "2026-10-22 12:30:00",
            "2026-10-22 13:30:00",
            "2026-10-22 13:30:00", # The fifth row should be dropped due to trip_duration_minutes < 0
            "2026-10-22 15:30:00",
        ]),
        "passenger_count": [1, 2, 0, 3, 1, 2],  # The third row should be dropped due to passenger_count <= 0
        "trip_distance": [5.0, 3.0, 2.0, 4.0, 1.0, 2.0],
        "fare_amount": [15.0, -5.0, 10.0, 20.0, 25.0, 30.0],  # The second row should be dropped due to fare_amount < 0
        "total_amount": [20.0, 15.0, 10.0, 25.0, 30.0, None],  # The sixth row should be dropped due to total_amount being NaN
    })
    df.to_parquet(input_file, index=False)

    # Call the transform function
    transform.transform(input_file, output_file)

    # Read the output file and check the results
    result_df = pd.read_parquet(output_file)

    expected_df = pd.DataFrame({
        "tpep_pickup_datetime": pd.to_datetime([
            "2026-10-22 10:00:00",
            "2026-10-22 13:00:00"
        ]),
        "tpep_dropoff_datetime": pd.to_datetime([
            "2026-10-22 10:30:00",
            "2026-10-22 13:30:00"
        ]),
        "passenger_count": [1, 3],
        "trip_distance": [5.0, 4.0],
        "fare_amount": [15.0, 20.0],
        "total_amount": [20.0, 25.0],
        "trip_duration_minutes": [30.0, 30.0],
        "pickup_date": pd.to_datetime([
            "2026-10-22",
            "2026-10-22"
        ]).date
    })

    pd.testing.assert_frame_equal(result_df, expected_df)