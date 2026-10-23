import os
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

import find_latest_available as discovery


def run_find_work(available, processed, environment=None):
    engine = MagicMock()
    env = {"BACKFILL": "false"}
    if environment:
        env.update(environment)

    with (
        patch.dict(os.environ, env),
        patch.object(discovery, "create_engine", return_value=engine),
        patch.object(discovery, "is_available", return_value=available),
        patch.object(
            discovery, "is_processed", return_value=processed
        ) as mocked_is_processed,
        patch.object(discovery, "date") as mocked_date,
    ):
        mocked_date.today.return_value = date(2026, 10, 22)
        result = discovery.find_work()

    return result, engine, mocked_is_processed


@pytest.mark.parametrize(
    "year, month, expected",
    [
        (2026, 1, (2025, 12)),
        (2026, 12, (2026, 11)),
    ],
)
def test_previous_month(year, month, expected):
    assert discovery.previous_month(year, month) == expected


def test_find_work_when_available_and_not_processed():
    result, engine, _ = run_find_work(available=True, processed=False)

    assert result["process"] is True
    assert result["year"] == 2026
    assert result["month"] == 10
    engine.dispose.assert_called_once()


def test_find_work_when_source_is_unavailable():
    result, engine, mocked_is_processed = run_find_work(
        available=False, processed=False
    )

    assert result["process"] is False
    mocked_is_processed.assert_not_called()
    engine.dispose.assert_called_once()


def test_find_work_when_source_is_already_processed():
    result, engine, _ = run_find_work(available=True, processed=True)

    assert result["process"] is False
    engine.dispose.assert_called_once()


def test_find_work_with_backfill():
    result, engine, mocked_is_processed = run_find_work(
        available=True,
        processed=False,
        environment={
            "BACKFILL": "true",
            "BACKFILL_YEAR": "2025",
            "BACKFILL_MONTH": "5",
        },
    )

    assert result["process"] is True
    assert result["year"] == 2025
    assert result["month"] == 5
    mocked_is_processed.assert_not_called()
    engine.dispose.assert_called_once()