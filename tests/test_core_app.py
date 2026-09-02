# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""App.open: first launch, loading, corruption recovery, the rollover catch-up."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core.app import App, StartupOutcome
from rature.core.migrations import FutureVersionError
from rature.core.session import LockedError
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
    assert app.quarantined_path == tmp_path / "data.json.bad-20260824-143207"
    assert app.quarantined_path.read_text(encoding="utf-8") == "not json"
    assert (tmp_path / "data.json").exists()


def test_quarantined_path_is_none_without_a_corruption(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    first_launch = App.open(tmp_path, clock=clock_at(now))
    assert first_launch.quarantined_path is None

    loaded = App.open(tmp_path, clock=clock_at(now))
    assert loaded.quarantined_path is None


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
    assert app.ensure_day() is None
    assert app.session.day is day_before
    assert not (tmp_path / "archive").exists()


def test_ensure_day_returns_the_archived_day_when_due(tmp_path: Path) -> None:
    save_now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(save_now))
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))
    archived = app.ensure_day()
    assert archived is not None
    assert archived.date == date(2026, 8, 23)
    assert app.session.day.date == date(2026, 8, 24)


def test_archives_is_empty_before_any_rollover(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.archives() == []


def test_archives_lists_dates_most_recent_first(tmp_path: Path) -> None:
    save_now = datetime(2026, 8, 20, 10, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(save_now))
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))
    app.ensure_day()
    assert app.archives() == [date(2026, 8, 20)]


def test_read_archive_returns_the_loaded_day(tmp_path: Path) -> None:
    save_now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(save_now))
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))
    app.ensure_day()
    assert app.read_archive(date(2026, 8, 23)).date == date(2026, 8, 23)


def test_read_archive_raises_for_an_unknown_date(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    with pytest.raises(FileNotFoundError):
        app.read_archive(date(2026, 8, 1))


def test_archived_session_wraps_the_loaded_day(tmp_path: Path) -> None:
    save_now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(save_now))
    app.add("finish the meson file")
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))
    app.ensure_day()
    session = app.archived_session(date(2026, 8, 23))
    assert [task.text for task in session.active] == ["finish the meson file"]


def test_archived_session_raises_for_an_unknown_date(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    with pytest.raises(FileNotFoundError):
        app.archived_session(date(2026, 8, 1))


def test_day_text_renders_the_current_day(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    task = app.add("buy bread")
    app.strike(task.id)
    assert app.day_text() == "Monday 24 August\n\n[x] 1  buy bread"


def test_archived_day_text_renders_an_archived_day(tmp_path: Path) -> None:
    save_now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(save_now))
    app.add("finish the meson file")
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))
    app.ensure_day()
    assert app.archived_day_text(date(2026, 8, 23)) == (
        "Sunday 23 August\n\n[ ] 1  finish the meson file"
    )


def test_archived_day_text_raises_for_an_unknown_date(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    with pytest.raises(FileNotFoundError):
        app.archived_day_text(date(2026, 8, 1))


def _two_archives(tmp_path: Path) -> App:
    """archive/2026-08-20 = ["call the dentist"], 2026-08-21 = ["answer the email"]."""
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 20, 10, 0, tzinfo=PARIS)))
    app.add("call the dentist")
    app.clock = clock_at(datetime(2026, 8, 21, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    app.add("answer the email")
    app.clock = clock_at(datetime(2026, 8, 22, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    return app


def test_search_archives_returns_only_days_with_a_match(tmp_path: Path) -> None:
    app = _two_archives(tmp_path)
    assert app.search_archives("dentist") == [date(2026, 8, 20)]
    assert app.search_archives("email") == [date(2026, 8, 21)]


def test_search_archives_with_no_match_returns_an_empty_list(tmp_path: Path) -> None:
    assert _two_archives(tmp_path).search_archives("helicopter") == []


def test_search_archives_blank_query_returns_every_archive(tmp_path: Path) -> None:
    app = _two_archives(tmp_path)
    assert app.search_archives("") == app.archives()
    assert app.search_archives("   ") == app.archives()


def test_search_archives_keeps_the_most_recent_first_order(tmp_path: Path) -> None:
    app = _two_archives(tmp_path)
    assert app.search_archives("the") == [date(2026, 8, 21), date(2026, 8, 20)]


def test_search_archives_is_accent_and_case_insensitive(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 20, 10, 0, tzinfo=PARIS)))
    app.add("Réparer le vélo")
    app.clock = clock_at(datetime(2026, 8, 21, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    assert app.search_archives("REPARER LE VELO") == [date(2026, 8, 20)]


def test_search_archives_matches_a_struck_task(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 20, 10, 0, tzinfo=PARIS)))
    task = app.add("finish the report")
    app.strike(task.id)
    app.clock = clock_at(datetime(2026, 8, 21, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    assert app.search_archives("report") == [date(2026, 8, 20)]


def test_search_archives_skips_an_unreadable_archive(tmp_path: Path) -> None:
    app = _two_archives(tmp_path)
    (tmp_path / "archive" / "2026-08-19.json").write_text("not json", encoding="utf-8")
    assert app.search_archives("dentist") == [date(2026, 8, 20)]


def test_search_archives_skips_a_future_version_archive(tmp_path: Path) -> None:
    app = _two_archives(tmp_path)
    (tmp_path / "archive" / "2026-08-19.json").write_text(
        '{"version": 99}', encoding="utf-8"
    )
    assert app.search_archives("dentist") == [date(2026, 8, 20)]


def test_search_archives_on_a_fresh_app_is_empty(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.search_archives("anything") == []


def test_add_saves_immediately(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    app.add("first")
    reloaded = load(data_dir=tmp_path).into_session()
    assert [task.text for task in reloaded.day.tasks] == ["first"]


def test_add_struck_saves_a_struck_task(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    task = app.add_struck("already done")
    reloaded = load(data_dir=tmp_path).into_session()
    assert task.num == 1
    assert reloaded.day.tasks[0].done is True
    assert reloaded.day.tasks[0].done_at == now


def test_mutation_wrappers_persist_through_a_full_walkthrough(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))

    task = app.add("draft")
    app.rename(task.id, "final")
    app.strike(task.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.day.tasks[0].text == "final"
    assert reloaded.day.tasks[0].done is True

    app.unstrike(task.id)
    other = app.add("second")
    app.move_before(other.id, task.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert [t.text for t in reloaded.day.tasks] == ["second", "final"]

    app.lock()
    assert load(data_dir=tmp_path).into_session().day.locked is True
    app.unlock()
    assert load(data_dir=tmp_path).into_session().day.locked is False

    item = app.add_to_reserve("someday")
    app.rename_reserve(item.id, "someday, renamed")
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.reserve[0].text == "someday, renamed"

    drawn = app.draw_from_reserve(item.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.reserve == []
    assert reloaded.day.tasks[-1].id == drawn.id

    other_item = app.add_to_reserve("gone")
    app.delete_from_reserve(other_item.id)
    assert load(data_dir=tmp_path).into_session().reserve == []

    app.delete(drawn.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert drawn.id not in [t.id for t in reloaded.day.tasks]
    assert len(reloaded.day.deletions) == 1

    app.undo_last_deletion()
    reloaded = load(data_dir=tmp_path).into_session()
    assert drawn.id in [t.id for t in reloaded.day.tasks]
    assert reloaded.day.deletions == []

    template = app.add_recurring("water plants", [0, 1, 2, 3, 4, 5, 6])
    app.edit_recurring(template.id, weekdays=[0, 3])
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.recurring[0].weekdays == [0, 3]

    app.delete_recurring(template.id)
    assert load(data_dir=tmp_path).into_session().recurring == []


def test_add_on_a_locked_list_raises_and_is_not_saved(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    app.lock()
    before = (tmp_path / "data.json").read_text(encoding="utf-8")
    with pytest.raises(LockedError):
        app.add("nope")
    assert (tmp_path / "data.json").read_text(encoding="utf-8") == before


def test_strike_an_unknown_task_raises_key_error(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    with pytest.raises(KeyError):
        app.strike("no-such-id")


def test_striking_twice_raises_value_error(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    task = app.add("thing")
    app.strike(task.id)
    with pytest.raises(ValueError):
        app.strike(task.id)
