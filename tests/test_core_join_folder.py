# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Joining a chosen folder (SPECIFICATION.md §2.9, §3.17).

A folder holding a data.json is taken as is, the local file set aside. A
folder without one receives memory, and the archives if it has no archive/.
Joining reads again first, like a gesture, and writes nothing when refused.
"""

import json
import logging
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core import storage
from rature.core.app import (
    App,
    DataFileUnreadableError,
    DataFolderUnreachableError,
    FolderChangedError,
    JoinOutcome,
    JoinRefusal,
    JoinRefusedError,
    examine_folder,
)
from rature.core.migrations import CURRENT_VERSION
from rature.core.session import Day
from rature.core.storage import Store, load, load_archive, save

PARIS = timezone(timedelta(hours=2))
MONDAY = date(2026, 8, 24)
TUESDAY = date(2026, 8, 25)
FORMATS = Path(__file__).parent / "data" / "formats"


def _on(day: date):
    return lambda: datetime(day.year, day.month, day.day, 10, 0, tzinfo=PARIS)


def _texts(app: App) -> list[str]:
    return [task.text for task in app.session.day.tasks]


def _listing(folder: Path) -> set[str]:
    return {path.name for path in folder.iterdir()}


@pytest.fixture
def local(tmp_path: Path) -> Path:
    """The previous data folder, with a day already written."""
    folder = tmp_path / "local"
    app = App.open(folder, clock=_on(MONDAY))
    app.add("local task")
    return folder


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """The folder being joined, empty."""
    chosen = tmp_path / "Sync" / "rature"
    chosen.mkdir(parents=True)
    return chosen


def _with_data(chosen: Path, text: str = "other device") -> None:
    other = App.start_empty(chosen, chosen=True, clock=_on(MONDAY))
    other.add(text)


def _join(app: App, folder: Path) -> JoinOutcome:
    """Join as the dialog does: examine, show, then join what was shown."""
    return app.join(app.examine(folder))


def _with_archive(data_dir: Path, day: date) -> None:
    storage.archive(Day(date=day), data_dir=data_dir)


# Examining


def test_the_preview_tells_what_the_folder_holds(local: Path, folder: Path) -> None:
    _with_data(folder)
    (folder / "archive").mkdir()
    (folder / "notes.txt").write_text("")

    preview = App.open(local, clock=_on(MONDAY)).examine(folder)

    assert preview.has_data
    assert preview.has_archive
    assert preview.other_files


def test_the_current_folder_is_refused_whatever_the_path(
    local: Path, tmp_path: Path
) -> None:
    alias = tmp_path / "alias"
    alias.symlink_to(local)
    app = App.open(local, clock=_on(MONDAY))

    with pytest.raises(JoinRefusedError) as refused:
        app.examine(alias)

    assert refused.value.reason is JoinRefusal.CURRENT_FOLDER
    assert refused.value.folder == alias


def test_a_current_folder_out_of_reach_is_not_the_one_examined(
    tmp_path: Path, folder: Path
) -> None:
    preview = examine_folder(folder, current=tmp_path / "gone")

    assert not preview.has_data


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        ("{not json", JoinRefusal.UNREADABLE),
        (json.dumps({"version": CURRENT_VERSION + 1}), JoinRefusal.NEWER_VERSION),
    ],
)
def test_a_data_file_that_does_not_load_is_refused(
    local: Path, folder: Path, content: str, reason: JoinRefusal
) -> None:
    (folder / "data.json").write_text(content)

    with pytest.raises(JoinRefusedError) as refused:
        App.open(local, clock=_on(MONDAY)).examine(folder)

    assert refused.value.reason is reason


def test_a_folder_out_of_reach_is_refused(local: Path, tmp_path: Path) -> None:
    with pytest.raises(JoinRefusedError) as refused:
        App.open(local, clock=_on(MONDAY)).examine(tmp_path / "gone")

    assert refused.value.reason is JoinRefusal.UNREACHABLE


def test_the_preview_names_the_set_aside_file(local: Path, folder: Path) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(MONDAY))

    shown = app.examine(folder)
    app.clock = _on(TUESDAY)
    outcome = app.join(shown)

    assert shown.set_aside_as == local / "data.json.20260824-100000.bak"
    assert outcome.set_aside == shown.set_aside_as


@pytest.mark.parametrize(
    ("their_data", "their_archive", "stays"),
    [(False, False, False), (False, True, True), (True, False, True)],
)
def test_the_preview_says_where_local_archives_stay(
    local: Path, folder: Path, *, their_data: bool, their_archive: bool, stays: bool
) -> None:
    _with_archive(local, date(2026, 8, 20))
    if their_data:
        _with_data(folder)
    if their_archive:
        (folder / "archive").mkdir()

    shown = App.open(local, clock=_on(MONDAY)).examine(folder)

    assert shown.archives_stay_in == (local if stays else None)


def test_a_pending_day_counts_as_a_local_archive(local: Path, folder: Path) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(MONDAY))
    app.clock = _on(TUESDAY)
    app.ensure_day()

    assert app.examine(folder).archives_stay_in == local


def test_without_local_data_the_preview_promises_nothing(
    tmp_path: Path, folder: Path
) -> None:
    _with_data(folder)

    shown = examine_folder(folder, current=tmp_path / "gone", clock=_on(MONDAY))

    assert shown.has_data
    assert shown.set_aside_as is None
    assert shown.archives_stay_in is None
    assert shown.examined_at == _on(MONDAY)()


# Taking the folder's data


def test_a_folder_with_data_is_taken_and_ours_set_aside(
    local: Path, folder: Path
) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(MONDAY))

    outcome = _join(app, folder)

    assert _texts(app) == ["other device"]
    assert app.data_dir == folder
    assert outcome.set_aside == local / "data.json.20260824-100000.bak"
    assert _listing(local) == {"data.json.20260824-100000.bak"}
    assert app.take_reloaded()
    assert not app.reread()


def test_local_archives_stay_behind_when_taking(local: Path, folder: Path) -> None:
    _with_archive(local, date(2026, 8, 20))
    _with_data(folder)

    _join(App.open(local, clock=_on(MONDAY)), folder)

    assert not (folder / "archive").exists()


def test_an_older_format_is_backed_up_in_the_folder_on_joining(
    local: Path, folder: Path
) -> None:
    shutil.copy(FORMATS / "v1.0.0" / "data.json", folder / "data.json")
    app = App.open(local, clock=_on(MONDAY))
    app.examine(folder)
    assert _listing(folder) == {"data.json"}

    _join(app, folder)

    assert "data.json.v1.bak" in _listing(folder)


def test_a_first_launch_takes_the_data_with_nothing_set_aside(
    tmp_path: Path, folder: Path
) -> None:
    _with_data(folder)
    local = tmp_path / "never created"
    app = App.open(local, clock=_on(MONDAY))

    outcome = _join(app, folder)

    assert _texts(app) == ["other device"]
    assert outcome.set_aside is None
    assert not local.exists()


def test_a_change_that_could_not_be_saved_is_replaced_with_a_warning(
    local: Path, folder: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(MONDAY))
    app._write_failed = True

    with caplog.at_level(logging.WARNING, logger="rature.core.app"):
        _join(app, folder)

    assert not app.write_failed
    assert "could not be saved" in caplog.text


def test_a_failed_load_leaves_the_previous_folder_alone(
    local: Path, folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shutil.copy(FORMATS / "v1.0.0" / "data.json", folder / "data.json")
    app = App.open(local, clock=_on(MONDAY))
    app.clock = _on(TUESDAY)
    app.ensure_day()
    shown = app.examine(folder)

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("read-only")

    monkeypatch.setattr(storage, "_back_up_before_migration", refuse)

    with pytest.raises(PermissionError):
        app.join(shown)

    assert _listing(local) == {"data.json"}
    assert app.data_dir == local


def test_a_failed_set_aside_stops_everything(
    local: Path, folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(MONDAY))

    def refuse(*_args: object, **_kwargs: object) -> Path:
        raise PermissionError("read-only")

    monkeypatch.setattr(storage, "set_aside", refuse)

    with pytest.raises(PermissionError):
        _join(app, folder)

    assert app.data_dir == local
    assert _texts(app) == ["local task"]
    assert not app.take_reloaded()


# Copying ours


def test_an_empty_folder_receives_our_data_and_archives(
    local: Path, folder: Path
) -> None:
    _with_archive(local, date(2026, 8, 20))
    app = App.open(local, clock=_on(MONDAY))

    outcome = _join(app, folder)

    assert load(data_dir=folder).day.tasks[0].text == "local task"
    assert load_archive(date(2026, 8, 20), data_dir=folder) == Day(
        date=date(2026, 8, 20)
    )
    assert outcome.set_aside is None
    assert (local / "data.json").exists()
    assert app.data_dir == folder
    assert app.take_reloaded()
    assert not app.reread()


def test_without_local_archives_no_archive_folder_is_made(
    local: Path, folder: Path
) -> None:
    _join(App.open(local, clock=_on(MONDAY)), folder)

    assert _listing(folder) == {"data.json"}


def test_an_archive_folder_already_there_is_left_alone(
    local: Path, folder: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _with_archive(local, date(2026, 8, 20))
    (folder / "archive").mkdir()
    theirs = folder / "archive" / "2026-08-20.json"
    theirs.write_text("theirs")

    with caplog.at_level(logging.WARNING, logger="rature.core.app"):
        _join(App.open(local, clock=_on(MONDAY)), folder)

    assert theirs.read_text() == "theirs"
    # The preview said so: nothing unexpected to log.
    assert "local archives stayed" not in caplog.text


def test_archives_left_behind_against_the_preview_are_logged(
    local: Path,
    folder: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _with_archive(local, date(2026, 8, 20))
    app = App.open(local, clock=_on(MONDAY))
    shown = app.examine(folder)
    assert shown.archives_stay_in is None
    # archive/ arrived during the join: copy_archives found it there.
    monkeypatch.setattr(storage, "copy_archives", lambda **_kwargs: False)

    with caplog.at_level(logging.WARNING, logger="rature.core.app"):
        app.join(shown)

    assert f"local archives stayed in {local}" in caplog.text


def test_a_first_launch_writes_its_empty_day_into_the_folder(
    tmp_path: Path, folder: Path
) -> None:
    local = tmp_path / "never created"
    app = App.open(local, clock=_on(MONDAY))

    outcome = _join(app, folder)

    assert load(data_dir=folder).day == Day(date=MONDAY)
    assert outcome == JoinOutcome(set_aside=None)
    assert not local.exists()


def test_a_failed_write_into_the_folder_stops_the_switch(
    local: Path, folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(local, clock=_on(MONDAY))

    def refuse(*_args: object, **_kwargs: object) -> str:
        raise OSError("disk full")

    monkeypatch.setattr(storage, "save", refuse)

    with pytest.raises(OSError, match="disk full"):
        _join(app, folder)

    assert app.data_dir == local


# Reading again first


def test_joining_reads_the_previous_folder_again_first(
    local: Path, folder: Path
) -> None:
    app = App.open(local, clock=_on(MONDAY))
    App.open(local, clock=_on(MONDAY)).add("written elsewhere")

    _join(app, folder)

    assert [task.text for task in load(data_dir=folder).day.tasks] == [
        "local task",
        "written elsewhere",
    ]


def test_a_failed_read_of_the_previous_folder_writes_nothing(
    local: Path, folder: Path
) -> None:
    app = App.open(local, clock=_on(MONDAY))
    (local / "data.json").write_text("{not json")

    with pytest.raises(DataFileUnreadableError):
        _join(app, folder)

    assert _listing(folder) == set()
    assert app.data_dir == local


def test_a_folder_now_refused_is_a_changed_folder(local: Path, folder: Path) -> None:
    app = App.open(local, clock=_on(MONDAY))
    shown = app.examine(folder)
    (folder / "data.json").write_text("{arriving")

    with pytest.raises(FolderChangedError) as changed:
        app.join(shown)

    assert changed.value.refusal is JoinRefusal.UNREADABLE
    assert changed.value.preview is None
    assert _listing(local) == {"data.json"}
    assert app.data_dir == local


def test_a_data_file_that_arrived_is_a_changed_folder(
    local: Path, folder: Path
) -> None:
    app = App.open(local, clock=_on(MONDAY))
    shown = app.examine(folder)
    _with_data(folder)
    before = _listing(folder)

    with pytest.raises(FolderChangedError) as changed:
        app.join(shown)

    assert changed.value.refusal is None
    assert changed.value.preview is not None
    assert changed.value.preview.has_data
    assert changed.value.preview.set_aside_as == local / (
        "data.json.20260824-100000.bak"
    )
    assert _listing(local) == {"data.json"}
    assert _listing(folder) == before
    assert app.data_dir == local


def test_the_changed_preview_can_be_joined(local: Path, folder: Path) -> None:
    app = App.open(local, clock=_on(MONDAY))
    shown = app.examine(folder)
    _with_data(folder)
    with pytest.raises(FolderChangedError) as changed:
        app.join(shown)
    assert changed.value.preview is not None

    app.join(changed.value.preview)

    assert _texts(app) == ["other device"]


def test_a_new_visible_file_is_a_changed_folder(local: Path, folder: Path) -> None:
    app = App.open(local, clock=_on(MONDAY))
    shown = app.examine(folder)
    (folder / "notes.txt").write_text("")

    with pytest.raises(FolderChangedError):
        app.join(shown)


# Days rolled over in memory


def test_pending_archives_go_to_the_previous_folder_then_along(
    local: Path, folder: Path
) -> None:
    app = App.open(local, clock=_on(MONDAY))
    app.clock = _on(TUESDAY)
    app.ensure_day()

    _join(app, folder)

    assert load_archive(MONDAY, data_dir=local).tasks[0].text == "local task"
    assert load_archive(MONDAY, data_dir=folder).tasks[0].text == "local task"


def test_pending_archives_stay_behind_when_taking(local: Path, folder: Path) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(MONDAY))
    app.clock = _on(TUESDAY)
    app.ensure_day()

    _join(app, folder)

    assert load_archive(MONDAY, data_dir=local).tasks[0].text == "local task"
    assert not (folder / "archive").exists()


def test_a_first_launch_keeps_no_pending_archive(tmp_path: Path, folder: Path) -> None:
    local = tmp_path / "never created"
    app = App.open(local, clock=_on(MONDAY))
    app.clock = _on(TUESDAY)
    app.ensure_day()

    _join(app, folder)

    assert not local.exists()
    assert _listing(folder) == {"data.json"}
    assert load(data_dir=folder).day.date == TUESDAY


def test_taken_data_from_yesterday_rolls_over_in_memory(
    local: Path, folder: Path
) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(TUESDAY))

    _join(app, folder)

    assert app.session.day.date == TUESDAY
    assert load(data_dir=folder).day.date == MONDAY


# After the switch


def test_the_undo_stack_empties_on_joining(local: Path, folder: Path) -> None:
    app = App.open(local, clock=_on(MONDAY))
    app.delete(app.session.day.tasks[0].id)
    assert app.can_undo

    _join(app, folder)

    assert not app.can_undo


def test_conflict_copies_are_looked_for_in_the_new_folder(
    local: Path, folder: Path
) -> None:
    (folder / "data.json.sync-conflict-20260824-100000-ABCDEFG").write_text("")
    app = App.open(local, clock=_on(MONDAY))
    assert not app.has_conflict_copies

    _join(app, folder)

    assert app.has_conflict_copies


def test_the_joined_folder_is_never_created_again(local: Path, folder: Path) -> None:
    app = App.open(local, clock=_on(MONDAY))
    _join(app, folder)
    shutil.rmtree(folder)

    with pytest.raises(DataFolderUnreachableError):
        app.add("after the folder went")

    assert not folder.exists()


def test_gestures_after_joining_write_to_the_folder(local: Path, folder: Path) -> None:
    _with_data(folder)
    app = App.open(local, clock=_on(MONDAY))
    _join(app, folder)

    app.add("after joining")

    assert [task.text for task in load(data_dir=folder).day.tasks] == [
        "other device",
        "after joining",
    ]


# Copying archives, storage alone


def test_only_archive_names_are_copied(tmp_path: Path, folder: Path) -> None:
    source = tmp_path / "source"
    _with_archive(source, date(2026, 8, 20))
    (source / "archive" / "notes.txt").write_text("")

    assert storage.copy_archives(source=source, target=folder)

    assert _listing(folder / "archive") == {"2026-08-20.json"}


def test_an_archive_already_there_is_kept(
    tmp_path: Path, folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # archive/ arrived between mkdir and the copy of one file.
    source = tmp_path / "source"
    _with_archive(source, date(2026, 8, 20))
    _with_archive(source, date(2026, 8, 21))
    write_new = storage._write_new

    def arrived_first(path: Path, content: bytes) -> bool:
        if path.name == "2026-08-20.json":
            path.write_text("theirs")
        return write_new(path, content)

    monkeypatch.setattr(storage, "_write_new", arrived_first)

    assert storage.copy_archives(source=source, target=folder)

    assert (folder / "archive" / "2026-08-20.json").read_text() == "theirs"
    assert load_archive(date(2026, 8, 21), data_dir=folder) == Day(
        date=date(2026, 8, 21)
    )
    assert _listing(folder / "archive") == {"2026-08-20.json", "2026-08-21.json"}


def test_no_local_archives_means_nothing_copied(tmp_path: Path, folder: Path) -> None:
    save(Store(day=Day(date=MONDAY)), data_dir=tmp_path / "source")

    assert not storage.copy_archives(source=tmp_path / "source", target=folder)
    assert _listing(folder) == set()


# Without local data


def test_a_first_launch_has_no_local_data(tmp_path: Path) -> None:
    app = App.open(tmp_path / "never created", clock=_on(MONDAY))

    assert not app.has_local_data


def test_a_first_gesture_makes_local_data(tmp_path: Path) -> None:
    app = App.open(tmp_path / "never created", clock=_on(MONDAY))
    app.add("first")

    assert app.has_local_data


def test_a_first_gesture_that_failed_to_write_counts_as_local_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(tmp_path / "never created", clock=_on(MONDAY))

    def refuse(*_args: object, **_kwargs: object) -> str:
        raise OSError("disk full")

    monkeypatch.setattr(storage, "save", refuse)
    with pytest.raises(OSError, match="disk full"):
        app.add("first")

    assert app.has_local_data


def test_a_loaded_file_is_local_data(local: Path) -> None:
    assert App.open(local, clock=_on(MONDAY)).has_local_data
