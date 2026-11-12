# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""A data folder the user chose (SPECIFICATION.md §2.9, §3.6 situation 2).

Never created, its rights never changed, and out of reach rather than a
first launch when it is gone. Also the read refused before a gesture, on
any folder, which is out of reach rather than a failed write.
"""

import os
import stat
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core import storage
from rature.core.app import (
    App,
    DataFileMissingError,
    DataFolderUnreachableError,
    StartupOutcome,
)
from rature.core.session import Day
from rature.core.storage import Store, load, save

PARIS = timezone(timedelta(hours=2))
MONDAY = date(2026, 8, 24)

_needs_permissions = pytest.mark.skipif(
    os.geteuid() == 0, reason="root ignores permissions"
)


def _on(day: date):
    return lambda: datetime(day.year, day.month, day.day, 10, 0, tzinfo=PARIS)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@pytest.fixture
def chosen(tmp_path: Path) -> Path:
    """A folder the user chose, already holding data, left at 0o755."""
    folder = tmp_path / "Sync" / "rature"
    folder.mkdir(parents=True)
    save(Store(day=Day(date=MONDAY)), data_dir=folder)
    folder.chmod(0o755)
    return folder


def _refuse(*_args: object, **_kwargs: object) -> bytes:
    raise PermissionError("no access")


def test_a_chosen_folder_that_is_gone_is_out_of_reach(tmp_path: Path) -> None:
    folder = tmp_path / "Sync" / "rature"

    with pytest.raises(DataFolderUnreachableError):
        App.open(folder, chosen=True)

    assert list(tmp_path.iterdir()) == []


def test_an_empty_chosen_folder_is_a_missing_file(tmp_path: Path) -> None:
    folder = tmp_path / "Sync"
    folder.mkdir()

    with pytest.raises(DataFileMissingError):
        App.open(folder, chosen=True)

    assert list(folder.iterdir()) == []


@_needs_permissions
def test_a_chosen_folder_that_refuses_access_is_out_of_reach(chosen: Path) -> None:
    chosen.parent.chmod(0o000)
    try:
        with pytest.raises(DataFolderUnreachableError):
            App.open(chosen, chosen=True)
    finally:
        chosen.parent.chmod(0o700)


def test_opening_a_chosen_folder_leaves_its_rights(chosen: Path) -> None:
    app = App.open(chosen, chosen=True, clock=_on(MONDAY))

    assert app.startup is StartupOutcome.LOADED
    assert _mode(chosen) == 0o755


def test_writing_to_a_chosen_folder_leaves_its_rights(chosen: Path) -> None:
    App.open(chosen, chosen=True, clock=_on(MONDAY)).add("buy bread")

    assert [task.text for task in load(data_dir=chosen).day.tasks] == ["buy bread"]
    assert _mode(chosen) == 0o755
    assert _mode(chosen / "data.json") == 0o600


def test_a_rollover_creates_archive_but_leaves_the_folders_rights(
    chosen: Path,
) -> None:
    App.open(chosen, chosen=True, clock=_on(MONDAY)).add("buy bread")

    App.open(chosen, chosen=True, clock=_on(MONDAY + timedelta(days=1))).add("next")

    assert (chosen / "archive" / f"{MONDAY.isoformat()}.json").exists()
    assert _mode(chosen) == 0o755


def test_a_chosen_folder_moved_while_running_is_never_created_again(
    chosen: Path,
) -> None:
    app = App.open(chosen, chosen=True, clock=_on(MONDAY))
    chosen.rename(chosen.with_name("moved"))

    with pytest.raises(DataFolderUnreachableError):
        app.add("never written")
    with pytest.raises(DataFolderUnreachableError):
        app.catch_up()
    with pytest.raises(DataFolderUnreachableError):
        app.try_again()

    assert not chosen.exists()


def test_start_empty_in_an_empty_chosen_folder_leaves_its_rights(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "Sync"
    folder.mkdir()
    folder.chmod(0o755)

    app = App.start_empty(folder, chosen=True, clock=_on(MONDAY))

    assert app.startup is StartupOutcome.STARTED_EMPTY
    assert load(data_dir=folder).day.tasks == []
    assert _mode(folder) == 0o755


def test_the_default_folder_is_still_born_with_the_first_gesture(
    data_dir: Path,
) -> None:
    app = App.open(data_dir, clock=_on(MONDAY))
    assert not data_dir.exists()

    app.add("first")

    assert (data_dir / "data.json").exists()
    assert _mode(data_dir) == 0o700


def test_save_never_creates_a_chosen_folder(tmp_path: Path) -> None:
    folder = tmp_path / "gone"

    with pytest.raises(FileNotFoundError):
        save(Store(day=Day(date=MONDAY)), data_dir=folder, create_data_dir=False)

    assert not folder.exists()


def test_archive_creates_archive_but_never_its_parent(tmp_path: Path) -> None:
    folder = tmp_path / "gone"
    with pytest.raises(FileNotFoundError):
        storage.archive(Day(date=MONDAY), data_dir=folder, create_data_dir=False)
    assert not folder.exists()

    folder.mkdir()
    storage.archive(Day(date=MONDAY), data_dir=folder, create_data_dir=False)
    assert (folder / "archive" / f"{MONDAY.isoformat()}.json").exists()


def test_a_read_refused_before_a_gesture_is_out_of_reach_on_any_folder(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(data_dir, clock=_on(MONDAY))
    app.add("buy bread")
    before = (data_dir / "data.json").read_bytes()
    monkeypatch.setattr(storage, "read_main", _refuse)

    with pytest.raises(DataFolderUnreachableError):
        app.add("never written")

    assert not app.write_failed
    assert (data_dir / "data.json").read_bytes() == before


def test_a_read_refused_on_try_again_is_out_of_reach(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = App.open(data_dir, clock=_on(MONDAY))
    app.add("buy bread")
    monkeypatch.setattr(storage, "read_main", _refuse)

    with pytest.raises(DataFolderUnreachableError):
        app.try_again()


def test_a_read_refused_on_return_of_focus_stays_an_oserror(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # SPECIFICATION.md §3.1: the window only logs it.
    app = App.open(data_dir, clock=_on(MONDAY))
    app.add("buy bread")
    monkeypatch.setattr(storage, "read_main", _refuse)

    with pytest.raises(PermissionError):
        app.catch_up()


def test_try_again_on_reachable_data_reads_as_reread(data_dir: Path) -> None:
    app = App.open(data_dir, clock=_on(MONDAY))
    app.add("buy bread")

    assert app.try_again() is False
