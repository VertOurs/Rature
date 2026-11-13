# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Data Folder… entry and the dialogs to join a folder (§3.17).

The dialogs stay real for everything they are told, only their answers are
played here, the portal's folder picker included.
"""

from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from gi.repository import Gio
from ui_helpers import (
    FakeAdwAlertDialog,
    FakeFileDialog,
    fake_folder_dialogs,
    process_events,
    type_into,
)

from rature.core.app import App
from rature.core.storage import load
from rature.ui import APP_ID, list_helpers
from rature.ui.application import RatureApplication
from rature.ui.archives_window import ArchivesWindow
from rature.ui.window import RatureWindow


@pytest.fixture(autouse=True)
def dialogs(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    fake_folder_dialogs(monkeypatch)
    yield
    Gio.Settings.new(APP_ID).reset("data-folder")


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """The folder being joined, empty."""
    chosen = tmp_path / "Sync" / "rature"
    chosen.mkdir(parents=True)
    return chosen


def _dialog() -> FakeAdwAlertDialog:
    return FakeAdwAlertDialog.shown[-1]


def _with_data(folder: Path, now: list[datetime]) -> None:
    App.start_empty(folder, chosen=True, clock=lambda: now[0]).add("other device")


def _choose(window: RatureWindow, folder: Path) -> None:
    window.activate_action("win.data-folder", None)
    _dialog().press("Choose a Folder…")
    FakeFileDialog.shown[-1].pick(folder)


def _shown(window: RatureWindow) -> list[str]:
    rows = list_helpers.rows(window.day_view.active_list)
    return [row.text_label.get_label() for row in rows]


def _setting() -> str:
    return Gio.Settings.new(APP_ID).get_string("data-folder")


def test_the_menu_entry_shows_the_data_folder(window: RatureWindow, app: App) -> None:
    window.activate_action("win.data-folder", None)

    dialog = _dialog()
    assert dialog.get_heading() == "Data Folder"
    assert dialog.get_body() == f"Rature keeps its data in: {app.data_dir}"
    assert dialog.labels() == ["Close", "Open Folder", "Choose a Folder…"]
    assert dialog.parent is window


def test_open_folder_opens_the_data_folder(
    window: RatureWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened = []
    monkeypatch.setattr(window, "_open_data_folder", lambda: opened.append(True))
    window.activate_action("win.data-folder", None)

    _dialog().press("Open Folder")

    assert opened == [True]
    assert FakeFileDialog.shown == []


def test_choose_a_folder_opens_the_portal_picker(window: RatureWindow) -> None:
    window.activate_action("win.data-folder", None)

    _dialog().press("Choose a Folder…")

    assert FakeFileDialog.shown[-1].parent is window


def test_a_dismissed_picker_changes_nothing(window: RatureWindow, app: App) -> None:
    window.activate_action("win.data-folder", None)
    _dialog().press("Choose a Folder…")
    before = len(FakeAdwAlertDialog.shown)

    FakeFileDialog.shown[-1].dismiss()

    assert len(FakeAdwAlertDialog.shown) == before
    assert _setting() == ""


def test_a_folder_with_data_is_taken(
    window: RatureWindow, app: App, folder: Path, now: list[datetime]
) -> None:
    type_into(window.day_view.entry, "local task")
    local = app.data_dir
    _with_data(folder, now)

    _choose(window, folder)

    dialog = _dialog()
    assert dialog.get_heading() == "Use the data in this folder?"
    assert dialog.get_body() == (
        "Your current data will be set aside as data.json.20260824-100000.bak, "
        "in the previous folder."
    )
    assert dialog.labels() == ["Cancel", "Use This Folder"]
    dialog.press("Use This Folder")

    assert app.data_dir == folder
    assert _setting() == str(folder)
    assert _shown(window) == ["other device"]
    assert (local / "data.json.20260824-100000.bak").exists()


def test_our_data_is_copied_into_a_folder_without_data(
    window: RatureWindow, app: App, folder: Path
) -> None:
    type_into(window.day_view.entry, "local task")

    _choose(window, folder)

    dialog = _dialog()
    assert dialog.get_heading() == "Copy your data to this folder?"
    assert dialog.get_body() == (
        "If this folder is synced, wait until its first sync "
        "has finished before copying."
    )
    dialog.press("Copy Data Here")

    assert load(data_dir=folder).day.tasks[0].text == "local task"
    assert _setting() == str(folder)
    assert _shown(window) == ["local task"]


def test_the_dialog_says_what_else_the_folder_holds(
    window: RatureWindow, app: App, folder: Path, now: list[datetime]
) -> None:
    type_into(window.day_view.entry, "local task")
    (folder / "archive").mkdir()
    (folder / "notes.txt").write_text("")
    now[0] += timedelta(days=1)
    app.ensure_day()  # yesterday becomes a local archive, pending

    _choose(window, folder)

    lines = _dialog().get_body().split("\n\n")
    assert lines[1:] == [
        f"Archives stay in the previous folder: {app.data_dir}",
        "This folder also contains other files.",
    ]


def test_a_first_launch_starts_the_folder_on_an_empty_day(
    window: RatureWindow, app: App, folder: Path, tmp_path: Path
) -> None:
    _choose(window, folder)

    dialog = _dialog()
    assert dialog.get_heading() == "Start from an empty day?"
    assert dialog.get_body().split("\n\n") == [
        "This empty day will also replace the data on your other synced devices.",
        "If this folder is synced, wait until its first sync "
        "has finished before copying.",
    ]
    assert dialog.labels() == ["Cancel", "Start Empty"]
    dialog.press("Start Empty")

    assert (folder / "data.json").exists()
    assert not (tmp_path / "rature").exists()
    assert app.data_dir == folder


def test_a_first_launch_takes_a_folder_with_data_without_a_set_aside(
    window: RatureWindow, app: App, folder: Path, now: list[datetime]
) -> None:
    _with_data(folder, now)

    _choose(window, folder)

    assert _dialog().get_body() == ""
    _dialog().press("Use This Folder")
    assert _shown(window) == ["other device"]


def test_cancel_changes_nothing(
    window: RatureWindow, app: App, folder: Path, now: list[datetime]
) -> None:
    type_into(window.day_view.entry, "local task")
    local = app.data_dir
    _with_data(folder, now)
    _choose(window, folder)

    _dialog().press("Cancel")

    assert app.data_dir == local
    assert _setting() == ""
    assert _shown(window) == ["local task"]


def test_the_current_folder_is_refused(window: RatureWindow, app: App) -> None:
    type_into(window.day_view.entry, "local task")

    _choose(window, app.data_dir)

    dialog = _dialog()
    assert dialog.get_heading() == "This folder cannot be used."
    assert dialog.get_body() == f"This is already the data folder: {app.data_dir}"
    assert dialog.labels() == ["Close"]


def test_an_unreadable_data_file_is_refused(window: RatureWindow, folder: Path) -> None:
    (folder / "data.json").write_text("{half delivered")

    _choose(window, folder)

    assert _dialog().get_body() == (
        f"Its data file cannot be read: {folder / 'data.json'}"
    )


def test_a_folder_that_changed_reopens_the_dialog(
    window: RatureWindow, app: App, folder: Path, now: list[datetime]
) -> None:
    type_into(window.day_view.entry, "local task")
    local = app.data_dir
    _choose(window, folder)
    copy = _dialog()
    _with_data(folder, now)  # the first sync delivers meanwhile

    copy.press("Copy Data Here")

    assert _dialog() is not copy
    assert _dialog().get_heading() == "Use the data in this folder?"
    assert app.data_dir == local
    assert load(data_dir=folder).day.tasks[0].text == "other device"
    _dialog().press("Use This Folder")
    assert _shown(window) == ["other device"]


def test_joining_closes_the_archives_windows(
    application: RatureApplication, window: RatureWindow, app: App, folder: Path
) -> None:
    type_into(window.day_view.entry, "local task")
    archives = ArchivesWindow(app=app, application=application, transient_for=window)
    archives.present()
    process_events()

    _choose(window, folder)
    _dialog().press("Copy Data Here")
    process_events()

    assert archives not in application.get_windows()
    assert window in application.get_windows()
