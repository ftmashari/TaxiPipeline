from unittest.mock import MagicMock, patch

import pandas as pd
from load import run


def test_run(tmp_path):
    # Mock the create_tables function and the engine
    mock_create_tables = MagicMock()
    mock_engine = MagicMock()

    df = pd.DataFrame({
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

    tmp_dir = tmp_path / "data" / "analytics" / "yellow"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(tmp_dir / "daily_metrics_2026-10.parquet", index=False)


    with patch("load.create_tables", mock_create_tables), \
        patch("load.create_engine", return_value=mock_engine), \
        patch("load.ANALYTICS_DIR", tmp_dir):
        run(2026, 10)

    # Assert that create_tables was called once with the mock engine
    mock_create_tables.assert_called_once_with(mock_engine)

    assert mock_engine.begin.called