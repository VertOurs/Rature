# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""XDG resolution, atomic round-trips and the never-overwrite archive rule."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core.models import Origin, RecurringItem, ReserveItem, Task
from rature.core.session import Day, Session
from rature.core.storage import (
    FILE_VERSION,
    Store,
    _atomic_write_json,
    archive,
    load,
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
    with pytest.raises(ValueError):
        load(data_dir=tmp_path)


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


def test_a_hand_written_task_round_trips(tmp_path: Path) -> None:
    day = Day(
        date=date(2026, 8, 24),
        counter=2,
        tasks=[Task(num=1, text="x", origin=Origin.RESERVE, source_id="abc")],
    )
    save(Store(day=day), data_dir=tmp_path)
    assert load(data_dir=tmp_path).day == day
