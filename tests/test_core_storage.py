# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""XDG resolution, atomic round-trips and the never-overwrite archive rule."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core.migrations import FutureVersionError
from rature.core.models import Origin, RecurringItem, ReserveItem, Task
from rature.core.session import Day, Session
from rature.core.storage import (
    FILE_VERSION,
    Store,
    _atomic_write_json,
    archive,
    list_archives,
    load,
    load_archive,
    quarantine,
    save,
    xdg_data_dir,
)

PARIS = timezone(timedelta(hours=2))
STAMP = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)


def make_store() -> Store:
    session = Session(Day(date=date(2026, 8, 24)))
    session.add("café résumé")
    done = session.add("done thing")
    session.strike(done.id, now=STAMP)
    dropped = session.add("dropped")
    session.delete(dropped.id, now=STAMP)
    return Store(
        day=session.day,
        reserve=[ReserveItem(text="someday", created=date(2026, 8, 20))],
        recurring=[RecurringItem(text="water plants", weekdays=[0, 3])],
    )


def test_xdg_data_dir_uses_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", "/somewhere/xdg")
    assert xdg_data_dir() == Path("/somewhere/xdg/rature")


def test_xdg_data_dir_falls_back_to_local_share(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/home/u")))
    assert xdg_data_dir() == Path("/home/u/.local/share/rature")


def test_save_then_load_round_trips(tmp_path: Path) -> None:
    store = make_store()
    save(store, data_dir=tmp_path)
    assert load(data_dir=tmp_path) == store


def test_save_creates_the_directory(tmp_path: Path) -> None:
    nested = tmp_path / "not" / "there" / "yet"
    save(make_store(), data_dir=nested)
    assert (nested / "data.json").is_file()


def test_save_leaves_no_temporary_file(tmp_path: Path) -> None:
    save(make_store(), data_dir=tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_a_failed_write_leaves_no_temporary_file(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        _atomic_write_json(tmp_path / "data.json", {"bad": object()})
    assert list(tmp_path.iterdir()) == []


def test_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load(data_dir=tmp_path)


def test_load_rejects_an_unknown_version(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text('{"version": 99}', encoding="utf-8")
    with pytest.raises(FutureVersionError):
        load(data_dir=tmp_path)


def test_quarantine_renames_the_main_file(tmp_path: Path) -> None:
    save(make_store(), data_dir=tmp_path)
    dest = quarantine(STAMP, data_dir=tmp_path)
    assert dest == tmp_path / "data.json.bad-20260824-143207"
    assert dest.exists()
    assert not (tmp_path / "data.json").exists()


def test_quarantine_preserves_the_content(tmp_path: Path) -> None:
    save(make_store(), data_dir=tmp_path)
    original = (tmp_path / "data.json").read_text(encoding="utf-8")
    dest = quarantine(STAMP, data_dir=tmp_path)
    assert dest.read_text(encoding="utf-8") == original


def test_quarantine_does_not_overwrite_a_same_second_collision(
    tmp_path: Path,
) -> None:
    (tmp_path / "data.json.bad-20260824-143207").write_text("first", encoding="utf-8")
    (tmp_path / "data.json").write_text("second", encoding="utf-8")
    dest = quarantine(STAMP, data_dir=tmp_path)
    assert dest == tmp_path / "data.json.bad-20260824-143207-2"
    assert dest.read_text(encoding="utf-8") == "second"
    assert (tmp_path / "data.json.bad-20260824-143207").read_text(
        encoding="utf-8"
    ) == "first"


def test_reserve_and_recurring_survive_the_round_trip(tmp_path: Path) -> None:
    save(make_store(), data_dir=tmp_path)
    loaded = load(data_dir=tmp_path)
    assert loaded.reserve[0].text == "someday"
    assert loaded.recurring[0].weekdays == [0, 3]


def test_accented_text_stays_readable(tmp_path: Path) -> None:
    save(make_store(), data_dir=tmp_path)
    text = (tmp_path / "data.json").read_text(encoding="utf-8")
    assert "café résumé" in text


def test_archive_is_named_after_the_day_date(tmp_path: Path) -> None:
    day = Day(date=date(2026, 8, 24))
    path = archive(day, data_dir=tmp_path)
    assert path == tmp_path / "archive" / "2026-08-24.json"


def test_archive_overwrites_the_same_date(tmp_path: Path) -> None:
    first = archive(Day(date=date(2026, 8, 24), counter=5), data_dir=tmp_path)
    second = archive(Day(date=date(2026, 8, 24), counter=9), data_dir=tmp_path)
    assert first == second
    assert json.loads(second.read_text(encoding="utf-8"))["counter"] == 9
    assert list((tmp_path / "archive").iterdir()) == [second]


def test_archive_carries_a_version(tmp_path: Path) -> None:
    path = archive(Day(date=date(2026, 8, 24)), data_dir=tmp_path)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == FILE_VERSION


def test_archive_keeps_the_deletion_journal(tmp_path: Path) -> None:
    session = Session(Day(date=date(2026, 8, 24)))
    gone = session.add("gone")
    session.delete(gone.id, now=STAMP)
    path = archive(session.day, data_dir=tmp_path)
    archived = json.loads(path.read_text(encoding="utf-8"))
    assert archived["deletions"][0]["text"] == "gone"


def test_list_archives_is_empty_without_an_archive_directory(tmp_path: Path) -> None:
    assert list_archives(data_dir=tmp_path) == []


def test_list_archives_orders_most_recent_first(tmp_path: Path) -> None:
    archive(Day(date=date(2026, 8, 20)), data_dir=tmp_path)
    archive(Day(date=date(2026, 8, 24)), data_dir=tmp_path)
    archive(Day(date=date(2026, 8, 22)), data_dir=tmp_path)
    assert list_archives(data_dir=tmp_path) == [
        date(2026, 8, 24),
        date(2026, 8, 22),
        date(2026, 8, 20),
    ]


def test_list_archives_ignores_a_corrupted_archives_content(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "2026-08-24.json").write_text("not json", encoding="utf-8")
    assert list_archives(data_dir=tmp_path) == [date(2026, 8, 24)]


def test_list_archives_ignores_a_non_dated_name(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "notes.json").write_text("{}", encoding="utf-8")
    assert list_archives(data_dir=tmp_path) == []


def test_list_archives_ignores_an_orphaned_tmp_file(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / ".2026-08-24.json.12345.tmp").write_text("{}", encoding="utf-8")
    assert list_archives(data_dir=tmp_path) == []


def test_list_archives_ignores_a_file_without_the_json_extension(
    tmp_path: Path,
) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "2026-08-24.txt").write_text("{}", encoding="utf-8")
    assert list_archives(data_dir=tmp_path) == []


def test_load_archive_returns_the_day(tmp_path: Path) -> None:
    day = Day(date=date(2026, 8, 24), counter=3)
    archive(day, data_dir=tmp_path)
    assert load_archive(date(2026, 8, 24), data_dir=tmp_path) == day


def test_load_archive_raises_for_a_missing_date(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_archive(date(2026, 8, 24), data_dir=tmp_path)


def test_load_archive_raises_for_invalid_json(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    (archive_dir / "2026-08-24.json").write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_archive(date(2026, 8, 24), data_dir=tmp_path)


def test_store_from_session_captures_the_three_parts() -> None:
    session = Session(Day(date=date(2026, 8, 24)))
    session.add("day task")
    session.add_to_reserve("later", today=date(2026, 8, 20))
    session.add_recurring("weekly", [2])
    store = Store.from_session(session)
    assert store.day is session.day
    assert store.reserve is session.reserve
    assert store.recurring is session.recurring


def test_store_into_session_hands_the_three_parts_back() -> None:
    store = make_store()
    session = store.into_session()
    assert session.day is store.day
    assert session.reserve is store.reserve
    assert session.recurring is store.recurring


def test_a_session_survives_save_from_session_then_into_session(tmp_path: Path) -> None:
    session = Session(Day(date=date(2026, 8, 24)))
    item = session.add_to_reserve("errand", today=date(2026, 8, 10))
    drawn = session.draw_from_reserve(item.id)
    save(Store.from_session(session), data_dir=tmp_path)
    loaded = load(data_dir=tmp_path).into_session()
    assert loaded.day.tasks[0].source_created == drawn.source_created


def test_a_hand_written_task_round_trips(tmp_path: Path) -> None:
    day = Day(
        date=date(2026, 8, 24),
        counter=2,
        tasks=[
            Task(
                num=1,
                text="x",
                origin=Origin.RESERVE,
                source_id="abc",
                source_created=date(2026, 8, 20),
            )
        ],
    )
    save(Store(day=day), data_dir=tmp_path)
    assert load(data_dir=tmp_path).day == day
