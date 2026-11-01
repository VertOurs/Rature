# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""App.open: first launch, loading, corruption recovery, the rollover catch-up."""

import logging
import os
import stat
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core import storage
from rature.core.app import App, EnsureOutcome, EnsureResult, StartupOutcome
from rature.core.migrations import FutureVersionError
from rature.core.session import LockedError
from rature.core.stats import DayCounts
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


def test_open_logs_the_data_directory(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="rature.core.app"):
        App.open(tmp_path)
    assert str(tmp_path) in caplog.text


def test_open_restricts_an_already_existing_directorys_permissions(
    tmp_path: Path,
) -> None:
    # ADR 0007 addendum: self-healing on every launch, not just mkdir's
    # exist_ok=True no-op on a directory that already existed loosely
    # permissioned from before this restriction, or an older version.
    tmp_path.chmod(0o755)
    App.open(tmp_path)
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o700


def test_open_survives_a_permission_restriction_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(storage, "restrict_data_dir_permissions", _raise_oserror)
    with caplog.at_level(logging.WARNING, logger="rature.core.app"):
        app = App.open(tmp_path)
    assert app.session.day is not None  # startup completed, not blocked
    assert caplog.records[0].levelno == logging.WARNING
    assert "permission" in caplog.text.lower()


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


# SPECIFICATION.md §3.6 situation 4: every startup OSError leaves App.open
# for the interface to alert and quit, and nothing is written meanwhile.

_needs_permissions = pytest.mark.skipif(
    os.geteuid() == 0, reason="root ignores permissions"
)


@_needs_permissions
def test_open_propagates_an_unreadable_data_file(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    App.open(tmp_path, clock=clock_at(now))
    path = tmp_path / "data.json"
    before = path.read_bytes()
    path.chmod(0o000)
    try:
        with pytest.raises(PermissionError):
            App.open(tmp_path, clock=clock_at(now))
    finally:
        path.chmod(0o600)
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


@_needs_permissions
def test_open_propagates_a_first_launch_into_a_read_only_directory(
    tmp_path: Path,
) -> None:
    tmp_path.chmod(0o500)
    try:
        with pytest.raises(OSError):
            App.open(tmp_path, clock=clock_at(datetime(2026, 8, 24, tzinfo=PARIS)))
    finally:
        tmp_path.chmod(0o700)
    assert list(tmp_path.iterdir()) == []


@_needs_permissions
def test_open_propagates_a_quarantine_it_cannot_perform(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text("not json", encoding="utf-8")
    tmp_path.chmod(0o500)
    try:
        with pytest.raises(OSError):
            App.open(tmp_path, clock=clock_at(datetime(2026, 8, 24, tzinfo=PARIS)))
    finally:
        tmp_path.chmod(0o700)
    assert (tmp_path / "data.json").read_text(encoding="utf-8") == "not json"


def test_open_propagates_an_archive_it_cannot_write_at_rollover(
    tmp_path: Path,
) -> None:
    # A plain file where archive/ should be: the rollover cannot archive,
    # so nothing is saved and the next launch replays it.
    monday = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    App.open(tmp_path, clock=clock_at(monday)).add("unfinished")
    before = (tmp_path / "data.json").read_bytes()
    (tmp_path / "archive").write_text("in the way", encoding="utf-8")
    with pytest.raises(OSError):
        App.open(tmp_path, clock=clock_at(monday + timedelta(days=1)))
    assert (tmp_path / "data.json").read_bytes() == before


def test_open_quarantines_invalid_json_and_starts_fresh(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text("not json", encoding="utf-8")
    now = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.startup is StartupOutcome.RECOVERED_FROM_CORRUPTION
    assert app.session.day.date == date(2026, 8, 24)
    assert app.quarantined_path == tmp_path / "data.json.bad-20260824-143207"
    assert app.quarantined_path.read_text(encoding="utf-8") == "not json"
    assert (tmp_path / "data.json").exists()


def test_open_logs_a_quarantine_at_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "data.json").write_text("not json", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="rature.core.app"):
        App.open(tmp_path)
    assert caplog.records[0].levelno == logging.WARNING
    assert "quarantin" in caplog.text.lower()


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


def test_a_rollover_is_logged(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    save_now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=PARIS)
    App.open(tmp_path, clock=clock_at(save_now))

    tomorrow_now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    with caplog.at_level(logging.INFO, logger="rature.core.app"):
        App.open(tmp_path, clock=clock_at(tomorrow_now))
    assert "2026-08-24" in caplog.text


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
    assert app.ensure_day() == EnsureResult(EnsureOutcome.IDLE, None)
    assert app.session.day is day_before
    assert not (tmp_path / "archive").exists()


def test_ensure_day_returns_the_archived_day_when_due(tmp_path: Path) -> None:
    save_now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(save_now))
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))
    result = app.ensure_day()
    assert result.outcome is EnsureOutcome.SAVED
    assert result.archived is not None
    assert result.archived.date == date(2026, 8, 23)
    assert app.session.day.date == date(2026, 8, 24)
    assert app.save_pending is False


def test_ensure_day_saves_the_prepared_list_in_the_new_day(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 23, 10, 0, tzinfo=PARIS)))
    prepared = app.add_to_tomorrow("prepared")
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))
    app.ensure_day()
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.tomorrow == []
    assert [(t.id, t.num) for t in reloaded.day.tasks] == [(prepared.id, 1)]
    archived = storage.load_archive(date(2026, 8, 23), data_dir=tmp_path)
    assert archived.tasks == []


def test_recurring_due_tomorrow_starts_from_the_reference_date(
    tmp_path: Path,
) -> None:
    # Tuesday 2026-08-25 at 02:00 still belongs to Monday: tomorrow is
    # Tuesday, not Wednesday.
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 24, 20, 0, tzinfo=PARIS)))
    tuesday = app.add_recurring("tuesday thing", [1])
    app.add_recurring("wednesday thing", [2])
    app.clock = clock_at(datetime(2026, 8, 25, 2, 0, tzinfo=PARIS))
    assert app.recurring_due_tomorrow() == [tuesday]


def _raise_oserror(*_args, **_kwargs):
    raise OSError("disk full")


def test_rollover_save_failure_is_retried_without_re_rolling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 23, 10, 0, tzinfo=PARIS)))
    app.add("carry me over")
    app.clock = clock_at(datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS))

    archive_calls = 0
    real_archive = storage.archive

    def counting_archive(day, **kwargs):
        nonlocal archive_calls
        archive_calls += 1
        return real_archive(day, **kwargs)

    monkeypatch.setattr(storage, "archive", counting_archive)
    monkeypatch.setattr(storage, "save", _raise_oserror)

    failed = app.ensure_day()
    assert failed.outcome is EnsureOutcome.SAVE_FAILED
    assert failed.archived is not None and failed.archived.date == date(2026, 8, 23)
    assert app.session.day.date == date(2026, 8, 24)  # rolled over in memory
    assert app.save_pending is True  # not treated as persisted
    assert archive_calls == 1
    assert load(data_dir=tmp_path).into_session().day.date == date(2026, 8, 23)

    monkeypatch.setattr(storage, "save", save)  # a working write again
    retried = app.ensure_day()
    assert retried.outcome is EnsureOutcome.SAVED
    assert retried.archived is None  # no second rollover
    assert archive_calls == 1  # not re-archived
    assert app.save_pending is False
    assert load(data_dir=tmp_path).into_session().day.date == date(2026, 8, 24)


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


def test_archive_session_from_wraps_a_day_the_caller_already_holds(
    tmp_path: Path,
) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 20, 10, 0, tzinfo=PARIS)))
    app.add("kept task")
    app.clock = clock_at(datetime(2026, 8, 21, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    day = app.read_archive(date(2026, 8, 20))
    session = app.archive_session_from(day)
    assert session.day is day
    assert [task.text for task in session.active] == ["kept task"]


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


def test_archive_matches_tests_an_already_loaded_day(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 20, 10, 0, tzinfo=PARIS)))
    app.add("Réparer le vélo")
    app.clock = clock_at(datetime(2026, 8, 21, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    day = app.read_archive(date(2026, 8, 20))
    assert app.archive_matches(day, "reparer") is True
    assert app.archive_matches(day, "helicopter") is False


def test_statistics_is_empty_without_archives(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))
    assert app.statistics() == []


def test_statistics_counts_each_archived_day_most_recent_first(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 20, 10, 0, tzinfo=PARIS)))
    done = app.add("done one")
    app.strike(done.id)
    app.add("left unfinished")
    gone = app.add("to be deleted")
    app.delete(gone.id)
    app.clock = clock_at(datetime(2026, 8, 21, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    app.add("only this one")
    app.clock = clock_at(datetime(2026, 8, 22, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    assert app.statistics() == [
        (date(2026, 8, 21), DayCounts(added=1, struck=0, deleted=0, to_reserve=1)),
        (date(2026, 8, 20), DayCounts(added=3, struck=1, deleted=1, to_reserve=1)),
    ]


def test_statistics_skips_an_unreadable_archive(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 20, 10, 0, tzinfo=PARIS)))
    app.add("kept")
    app.clock = clock_at(datetime(2026, 8, 21, 10, 0, tzinfo=PARIS))
    app.ensure_day()
    (tmp_path / "archive" / "2026-08-19.json").write_text("not json", encoding="utf-8")
    assert app.statistics() == [
        (date(2026, 8, 20), DayCounts(added=1, struck=0, deleted=0, to_reserve=1)),
    ]


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

    sent = app.add("send back")
    back = app.send_to_reserve(sent.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert sent.id not in [t.id for t in reloaded.day.tasks]
    assert reloaded.reserve == [back]
    app.delete_from_reserve(back.id)

    first, second = app.add_to_reserve("first"), app.add_to_reserve("second")
    app.move_reserve_before(second.id, first.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert [i.text for i in reloaded.reserve] == ["second", "first"]
    app.delete_from_reserve(first.id)
    app.delete_from_reserve(second.id)

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


def test_tomorrow_wrappers_persist(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))

    first = app.add_to_tomorrow("draft")
    second = app.add_to_tomorrow("second")
    app.rename_tomorrow(first.id, "final")
    app.set_tomorrow_priority(first.id, priority=True)
    app.move_tomorrow_before(second.id, first.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert [t.text for t in reloaded.tomorrow] == ["second", "final"]
    assert [t.priority for t in reloaded.tomorrow] == [False, True]

    app.delete_from_tomorrow(first.id)
    assert load(data_dir=tmp_path).into_session().tomorrow == [second]


def test_tomorrow_moves_persist(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=clock_at(now))

    task = app.add("later")
    prepared = app.move_to_tomorrow(task.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.day.tasks == []
    assert reloaded.tomorrow == [prepared]

    back = app.move_to_today(prepared.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.tomorrow == []
    assert reloaded.day.tasks == [back]

    item = app.add_to_reserve("someday")
    from_reserve = app.move_reserve_to_tomorrow(item.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.reserve == []
    assert reloaded.tomorrow == [from_reserve]

    returned = app.send_tomorrow_to_reserve(from_reserve.id)
    reloaded = load(data_dir=tmp_path).into_session()
    assert reloaded.tomorrow == []
    assert reloaded.reserve == [returned]
    assert returned.id == item.id


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


def test_open_removes_temporary_files_left_by_a_crash(tmp_path: Path) -> None:
    (tmp_path / "archive").mkdir()
    stale_main = tmp_path / ".data.json.4242.tmp"
    stale_archive = tmp_path / "archive" / ".2026-08-24.json.4242.tmp"
    delivery = tmp_path / ".syncthing.data.json.tmp"
    for path in (stale_main, stale_archive, delivery):
        path.write_text("{}")

    App.open(tmp_path)

    assert not stale_main.exists()
    assert not stale_archive.exists()
    assert delivery.exists()


def test_undo_follows_this_devices_deletions_most_recent_first(tmp_path: Path) -> None:
    app = App.open(tmp_path)
    assert app.can_undo is False
    first, second = app.add("first"), app.add("second")
    app.delete(first.id)
    app.delete(second.id)

    assert app.undo_last_deletion().id == second.id
    assert app.can_undo is True
    assert app.undo_last_deletion().id == first.id
    assert app.can_undo is False
    with pytest.raises(ValueError):
        app.undo_last_deletion()


def test_undo_leaves_another_devices_journal_entry_alone(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 14, 0, 0, tzinfo=PARIS)
    elsewhere = App.open(tmp_path, clock=clock_at(now))
    theirs = elsewhere.add("deleted elsewhere")
    elsewhere.delete(theirs.id)

    app = App.open(tmp_path, clock=clock_at(now))
    assert app.can_undo is False  # the journal holds an entry, none of ours

    ours = app.add("deleted here")
    app.delete(ours.id)
    assert app.undo_last_deletion().id == ours.id

    assert [entry.id for entry in app.session.day.deletions] == [theirs.id]
    assert app.can_undo is False


def test_a_refused_deletion_leaves_the_undo_stack_unchanged(tmp_path: Path) -> None:
    app = App.open(tmp_path)
    with pytest.raises(KeyError):
        app.delete("unknown")
    assert app.can_undo is False


def test_a_deletion_whose_write_failed_stays_undoable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(tmp_path)
    task = app.add("thing")
    monkeypatch.setattr(storage, "save", _raise_oserror)

    with pytest.raises(OSError):
        app.delete(task.id)

    assert app.can_undo is True
    monkeypatch.setattr(storage, "save", save)
    assert app.undo_last_deletion().id == task.id


def test_an_undo_whose_write_failed_leaves_the_stack_without_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(tmp_path)
    earlier, task = app.add("earlier"), app.add("thing")
    app.delete(earlier.id)
    app.delete(task.id)
    monkeypatch.setattr(storage, "save", _raise_oserror)

    with pytest.raises(OSError):
        app.undo_last_deletion()

    # Restored in memory: a second click undoes the earlier deletion, and
    # never raises KeyError on an entry that has already left the journal.
    assert task.id in [t.id for t in app.session.day.tasks]
    assert app.can_undo is True
    with pytest.raises(OSError):
        app.undo_last_deletion()
    assert earlier.id in [t.id for t in app.session.day.tasks]
    assert app.can_undo is False


def test_the_day_rollover_empties_the_undo_stack(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 24, 3, 0, tzinfo=PARIS)))
    task = app.add("deleted before 04:00")
    app.delete(task.id)
    app.clock = clock_at(datetime(2026, 8, 24, 4, 30, tzinfo=PARIS))

    app.ensure_day()

    assert app.can_undo is False


def test_the_undo_stack_is_empty_even_if_archiving_the_day_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(tmp_path, clock=clock_at(datetime(2026, 8, 24, 3, 0, tzinfo=PARIS)))
    task = app.add("deleted before 04:00")
    app.delete(task.id)
    app.clock = clock_at(datetime(2026, 8, 24, 4, 30, tzinfo=PARIS))
    monkeypatch.setattr(storage, "archive", _raise_oserror)

    with pytest.raises(OSError):
        app.ensure_day()

    assert app.can_undo is False
