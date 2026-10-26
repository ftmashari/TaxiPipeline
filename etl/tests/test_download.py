from unittest.mock import Mock

import download


def mock_month_response(monkeypatch, available=True):
    response = Mock()
    response.status_code = 200 if available else 403
    response.content = b"mocked content"

    if not available:
        response.raise_for_status.side_effect = download.requests.HTTPError(
            "HTTP error"
        )

    monkeypatch.setattr(
        download.requests,
        "get",
        lambda *args, **kwargs: response,
    )


def test_download_month_when_available(tmp_path, monkeypatch):
    monkeypatch.setattr(download, "RAW_DIR", tmp_path)
    mock_month_response(monkeypatch)

    year, month = 2026, 10
    result = download.download_month(year, month)

    expected_file = tmp_path / f"yellow_tripdata_{year}-{month:02d}.parquet"
    assert result == expected_file
    assert expected_file.exists()


def test_download_month_when_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(download, "RAW_DIR", tmp_path)
    mock_month_response(monkeypatch, available=False)

    assert download.download_month(2026, 10) is None


def test_download_month_when_file_already_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(download, "RAW_DIR", tmp_path)
    mock_month_response(monkeypatch)

    year, month = 2026, 10
    existing_file = tmp_path / f"yellow_tripdata_{year}-{month:02d}.parquet"
    existing_file.write_bytes(b"existing content")

    result = download.download_month(year, month)

    assert result == existing_file
    assert existing_file.read_bytes() == b"existing content"