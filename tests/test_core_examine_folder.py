# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Looking at a folder before joining it (SPECIFICATION.md §3.17).

The examination writes nothing, and only visible names count.
"""

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from rature.core.migrations import CURRENT_VERSION, FutureVersionError
from rature.core.session import Day
from rature.core.storage import Store, examine_folder, save

FORMATS = Path(__file__).parent / "data" / "formats"


def _listing(folder: Path) -> set[str]:
    return {path.name for path in folder.iterdir()}


def test_an_empty_folder_holds_nothing(tmp_path: Path) -> None:
    contents = examine_folder(tmp_path)

    assert contents.main is None
    assert not contents.has_archive
    assert not contents.other_files


def test_syncthing_entries_and_dot_files_are_not_visible(tmp_path: Path) -> None:
    (tmp_path / ".stfolder").mkdir()
    (tmp_path / ".stversions").mkdir()
    (tmp_path / ".stignore").write_text(".*.tmp\n")
    (tmp_path / ".hidden").write_text("")

    contents = examine_folder(tmp_path)

    assert not contents.other_files


def test_a_valid_data_file_comes_back_as_its_bytes(tmp_path: Path) -> None:
    save(Store(day=Day(date=date(2026, 8, 24))), data_dir=tmp_path)

    contents = examine_folder(tmp_path)

    assert contents.main == (tmp_path / "data.json").read_bytes()
    assert not contents.other_files


def test_an_archive_folder_alone_is_seen(tmp_path: Path) -> None:
    (tmp_path / "archive").mkdir()

    contents = examine_folder(tmp_path)

    assert contents.main is None
    assert contents.has_archive
    assert not contents.other_files


@pytest.mark.parametrize("name", ["notes.txt", "data.json.sync-conflict-x", "photos"])
def test_any_other_visible_entry_is_reported(tmp_path: Path, name: str) -> None:
    (tmp_path / name).write_text("")

    assert examine_folder(tmp_path).other_files


def test_an_older_format_is_accepted_without_a_backup(tmp_path: Path) -> None:
    shutil.copy(FORMATS / "v1.0.0" / "data.json", tmp_path / "data.json")

    contents = examine_folder(tmp_path)

    assert contents.main is not None
    assert _listing(tmp_path) == {"data.json"}


def test_an_unreadable_data_file_raises(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text("{not json")

    with pytest.raises(ValueError):
        examine_folder(tmp_path)


def test_a_newer_data_file_raises(tmp_path: Path) -> None:
    save(Store(day=Day(date=date(2026, 8, 24))), data_dir=tmp_path)
    path = tmp_path / "data.json"
    data = json.loads(path.read_text())
    path.write_text(json.dumps({**data, "version": CURRENT_VERSION + 1}))

    with pytest.raises(FutureVersionError):
        examine_folder(tmp_path)


def test_a_folder_that_is_gone_raises(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        examine_folder(tmp_path / "gone")
