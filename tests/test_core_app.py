# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""App.open: first launch, loading, corruption recovery, the rollover catch-up."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core.app import App, StartupOutcome
from rature.core.migrations import FutureVersionError
from rature.core.storage import Store, load, save

PARIS = timezone(timedelta(hours=2))


def clock_at(moment: datetime):
    return lambda: moment


def test_open_default_clock_is_timezone_aware(tmp_path: Path) -> None:
    app = App.open(tmp_path)
    assert app.clock().tzinfo is not None


def test_first_launch_creates_the_file_immediately(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.startup is StartupOutcome.FIRST_LAUNCH
    assert app.session.day.date == date(2026, 8, 24)
    assert (tmp_path / "data.json").exists()


def test_first_launch_uses_the_reference_date_not_the_calendar_date(
    tmp_path: Path,
) -> None:
    # 01:00 local is still the previous day, the boundary is 04:00.
    now = datetime(2026, 8, 25, 1, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.session.day.date == date(2026, 8, 24)


def test_open_loads_an_existing_file(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    session = App.open(tmp_path, clock=clock_at(now)).session
    session.add("keep me")
    save(Store.from_session(session), data_dir=tmp_path)

    app = App.open(tmp_path, clock=clock_at(now))
    assert app.startup is StartupOutcome.LOADED
    assert [task.text for task in app.session.day.tasks] == ["keep me"]


def test_open_propagates_a_future_version_and_builds_no_app(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text('{"version": 99}', encoding="utf-8")
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    with pytest.raises(FutureVersionError):
        App.open(tmp_path, clock=clock_at(now))
    # Nothing written, nothing moved.
    assert (tmp_path / "data.json").read_text(encoding="utf-8") == '{"version": 99}'
    assert list(tmp_path.iterdir()) == [tmp_path / "data.json"]


def test_open_quarantines_invalid_json_and_starts_fresh(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text("not json", encoding="utf-8")
    now = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.startup is StartupOutcome.RECOVERED_FROM_CORRUPTION
    assert app.session.day.date == date(2026, 8, 24)
    assert (tmp_path / "data.json.bad-20260824-143207").read_text(
        encoding="utf-8"
    ) == "not json"
    assert (tmp_path / "data.json").exists()


def test_open_quarantines_a_missing_field_and_starts_fresh(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text('{"version": 1}', encoding="utf-8")
    now = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.startup is StartupOutcome.RECOVERED_FROM_CORRUPTION
    assert (tmp_path / "data.json.bad-20260824-143207").exists()


def test_open_runs_a_due_rollover_before_returning(tmp_path: Path) -> None:
    yesterday = date(2026, 8, 23)
    save_now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=PARIS)
    App.open(tmp_path, clock=clock_at(save_now))  # first launch, day = 2026-08-23
    session = load(data_dir=tmp_path).into_session()
    assert session.day.date == yesterday

    tomorrow_now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(tomorrow_now))
    assert app.startup is StartupOutcome.LOADED
    assert app.session.day.date == date(2026, 8, 24)
    assert (tmp_path / "archive" / "2026-08-23.json").exists()


def test_open_multi_day_catch_up_runs_once(tmp_path: Path) -> None:
    save_now = datetime(2026, 8, 20, 10, 0, 0, tzinfo=PARIS)
    App.open(tmp_path, clock=clock_at(save_now))  # day = 2026-08-20

    days_later = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(days_later))
    assert app.session.day.date == date(2026, 8, 24)
    assert (tmp_path / "archive" / "2026-08-20.json").exists()
    for skipped in ("2026-08-21", "2026-08-22", "2026-08-23"):
        assert not (tmp_path / "archive" / f"{skipped}.json").exists()


def test_ensure_day_is_a_no_op_when_nothing_is_due(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    day_before = app.session.day
    app.ensure_day()
    assert app.session.day is day_before
    assert not (tmp_path / "archive").exists()
