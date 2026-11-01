# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Read before write (SPECIFICATION.md §2.9): two devices, one synced folder.

Each device is an App with its own clock. Sharing a temporary folder stands
in for the sync tool having delivered the file.
"""

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core import storage
from rature.core.app import (
    App,
    DataFileMissingError,
    DataFileUnreadableError,
    GestureRefusedError,
)
from rature.core.migrations import FutureVersionError
from rature.core.session import Session
from rature.core.storage import Store, load, load_archive

PARIS = timezone(timedelta(hours=2))
MONDAY = date(2026, 8, 24)
TUESDAY = date(2026, 8, 25)


def _on(day: date):
    return lambda: datetime(day.year, day.month, day.day, 10, 0, tzinfo=PARIS)


def _device(data_dir: Path, day: date = MONDAY) -> App:
    return App.open(data_dir, clock=_on(day))


def _as_dict(session: Session) -> dict:
    return Store.from_session(session).to_dict()


def _wake_on_tuesday(app: App) -> None:
    app.clock = _on(TUESDAY)
    assert app.ensure_day() is not None


def _main_bytes(data_dir: Path) -> bytes:
    return (data_dir / "data.json").read_bytes()


def test_a_gesture_applies_to_what_the_other_device_wrote(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    desktop = _device(data_dir)
    desktop.add("from the desktop")

    laptop.add("second from the laptop")

    assert [task.text for task in load(data_dir=data_dir).day.tasks] == [
        "from the laptop",
        "from the desktop",
        "second from the laptop",
    ]


def test_waking_up_before_the_delivery_loses_nothing(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    desktop = _device(data_dir)
    _wake_on_tuesday(laptop)
    desktop.add("evening, on the desktop")

    laptop.add("first gesture of tuesday")

    archived = load_archive(MONDAY, data_dir=data_dir)
    assert [task.text for task in archived.tasks] == [
        "from the laptop",
        "evening, on the desktop",
    ]
    stored = load(data_dir=data_dir)
    assert stored.day.date == TUESDAY
    assert [task.text for task in stored.day.tasks] == ["first gesture of tuesday"]


def test_a_gesture_on_a_task_redrawn_by_the_second_rollover_is_refused(
    data_dir: Path,
) -> None:
    laptop = _device(data_dir)
    laptop.add_recurring("water the plants", [TUESDAY.weekday()])
    desktop = _device(data_dir)
    _wake_on_tuesday(laptop)
    drawn_first = laptop.session.day.tasks[0]
    assert drawn_first.text == "water the plants"
    desktop.add("evening, on the desktop")
    before = _main_bytes(data_dir)

    with pytest.raises(GestureRefusedError):
        laptop.strike(drawn_first.id)

    assert _main_bytes(data_dir) == before
    assert laptop.session.day.date == TUESDAY
    redrawn = laptop.session.day.tasks[0]
    assert redrawn.text == "water the plants"
    assert redrawn.id != drawn_first.id
    assert not redrawn.done


def test_undo_is_refused_once_the_other_device_wrote_the_rollover(
    data_dir: Path,
) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    laptop.delete(laptop.session.day.tasks[0].id)
    assert laptop.can_undo
    desktop = _device(data_dir, TUESDAY)
    desktop.add("from the desktop")
    before = _main_bytes(data_dir)

    with pytest.raises(GestureRefusedError):
        laptop.undo_last_deletion()

    assert _main_bytes(data_dir) == before
    assert not laptop.can_undo
    assert laptop.session.day.date == TUESDAY


def test_a_file_from_a_future_version_stops_the_gesture_unwritten(
    data_dir: Path,
) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    in_memory = _as_dict(laptop.session)
    path = data_dir / "data.json"
    raw = json.loads(path.read_text())
    raw["version"] += 1
    path.write_text(json.dumps(raw))
    before = path.read_bytes()

    with pytest.raises(FutureVersionError):
        laptop.add("never written")

    assert path.read_bytes() == before
    assert _as_dict(laptop.session) == in_memory
    assert storage.list_archives(data_dir=data_dir) == []


def test_a_refused_gesture_leaves_memory_as_the_file_reads(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    target = laptop.session.day.tasks[0].id
    desktop = _device(data_dir)
    desktop.delete(target)
    desktop.add("from the desktop")

    with pytest.raises(GestureRefusedError):
        laptop.rename(target, "too late")

    assert _as_dict(laptop.session) == load(data_dir=data_dir).to_dict()


def test_a_refused_gesture_that_changed_memory_first_is_taken_back(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    _device(data_dir).add("from the desktop")
    real_rename = Session.rename

    def rename_then_fail(session: Session, task_id: str, text: str) -> None:
        real_rename(session, task_id, text)
        raise ValueError("refused halfway")

    monkeypatch.setattr(Session, "rename", rename_then_fail)
    target = laptop.session.day.tasks[0].id

    with pytest.raises(GestureRefusedError):
        laptop.rename(target, "half done")

    assert _as_dict(laptop.session) == load(data_dir=data_dir).to_dict()


def test_a_refusal_on_unchanged_data_stays_the_error_it_is(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    session = laptop.session

    with pytest.raises(KeyError):
        laptop.strike("no such task")

    assert laptop.session is session
    assert not laptop.take_reloaded()


def test_undo_never_moves_to_an_older_deletion(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("older")
    laptop.add("newer")
    older, newer = (task.id for task in laptop.session.day.tasks)
    laptop.delete(older)
    laptop.delete(newer)
    desktop = _device(data_dir)
    desktop.session.undo_deletion(newer)
    storage.save(Store.from_session(desktop.session), data_dir=data_dir)

    with pytest.raises(GestureRefusedError):
        laptop.undo_last_deletion()
    assert [task.id for task in laptop.session.day.tasks] == [newer]
    assert laptop.can_undo

    assert laptop.undo_last_deletion().id == older


def test_undo_empties_the_stack_only_after_succeeding(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    laptop.delete(laptop.session.day.tasks[0].id)
    _device(data_dir).add("from the desktop")

    assert laptop.undo_last_deletion().text == "from the laptop"

    assert not laptop.can_undo
    assert [task.text for task in load(data_dir=data_dir).day.tasks] == [
        "from the laptop",
        "from the desktop",
    ]


def test_undo_with_nothing_on_the_stack_reads_nothing(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    laptop = _device(data_dir)

    def never(**_kwargs: object) -> bytes:
        raise AssertionError("no read expected")

    monkeypatch.setattr(storage, "read_main", never)
    with pytest.raises(ValueError, match="no deletion"):
        laptop.undo_last_deletion()


def test_a_due_rollover_waits_on_an_unchanged_file(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    laptop.clock = _on(TUESDAY)

    laptop.add("still monday")

    assert laptop.session.day.date == MONDAY
    assert load(data_dir=data_dir).day.date == MONDAY


def test_a_new_modification_time_alone_changes_nothing(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    session = laptop.session
    os.utime(data_dir / "data.json", (0, 0))

    laptop.add("second")

    assert laptop.session is session
    assert not laptop.take_reloaded()


def test_this_devices_own_writes_are_not_reloads(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("first")
    session = laptop.session

    laptop.add("second")

    assert laptop.session is session
    assert not laptop.take_reloaded()


def test_a_fresh_file_is_reported_once(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    _device(data_dir).add("from the desktop")

    laptop.add("second from the laptop")

    assert laptop.take_reloaded()
    assert not laptop.take_reloaded()


def test_a_file_that_arrives_after_a_first_launch_is_taken(data_dir: Path) -> None:
    laptop = _device(data_dir)
    _device(data_dir).add("from the desktop")

    laptop.add("from the laptop")

    assert [task.text for task in load(data_dir=data_dir).day.tasks] == [
        "from the desktop",
        "from the laptop",
    ]


def test_a_file_that_vanished_stops_the_gesture_unwritten(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    (data_dir / "data.json").unlink()

    with pytest.raises(DataFileMissingError):
        laptop.add("never written")

    assert not (data_dir / "data.json").exists()


def test_a_file_that_no_longer_loads_stops_the_gesture_unwritten(
    data_dir: Path,
) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    (data_dir / "data.json").write_text("not json")

    with pytest.raises(DataFileUnreadableError):
        laptop.add("never written")

    assert (data_dir / "data.json").read_text() == "not json"


def _fail_next_save(app: App, monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    def disk_full(*_args: object, **_kwargs: object) -> str:
        raise OSError("disk full")

    with monkeypatch.context() as patch:
        patch.setattr(storage, "save", disk_full)
        with pytest.raises(OSError, match="disk full"):
            app.add(text)


def test_fresh_data_replacing_an_unsaved_gesture_leaves_a_warning(
    data_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    _fail_next_save(laptop, monkeypatch, "secret, never saved")
    _device(data_dir).add("from the desktop")

    with caplog.at_level(logging.WARNING, logger="rature.core.app"):
        laptop.add("second from the laptop")

    assert "could not be saved" in caplog.text
    assert "secret" not in caplog.text
    assert [task.text for task in load(data_dir=data_dir).day.tasks] == [
        "from the laptop",
        "from the desktop",
        "second from the laptop",
    ]


def test_an_unsaved_gesture_survives_on_an_unchanged_file(
    data_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    _fail_next_save(laptop, monkeypatch, "kept in memory")

    with caplog.at_level(logging.WARNING, logger="rature.core.app"):
        laptop.add("written with it")

    assert "could not be saved" not in caplog.text
    assert [task.text for task in load(data_dir=data_dir).day.tasks] == [
        "from the laptop",
        "kept in memory",
        "written with it",
    ]


def test_pending_archives_of_replaced_data_are_dropped(data_dir: Path) -> None:
    laptop = _device(data_dir)
    laptop.add("from the laptop")
    desktop = _device(data_dir, TUESDAY)
    _wake_on_tuesday(laptop)
    desktop.add("from the desktop")

    laptop.add("second gesture of tuesday")

    assert storage.list_archives(data_dir=data_dir) == [MONDAY]
    assert [task.text for task in load_archive(MONDAY, data_dir=data_dir).tasks] == [
        "from the laptop"
    ]
    assert [task.text for task in load(data_dir=data_dir).day.tasks] == [
        "from the desktop",
        "second gesture of tuesday",
    ]
