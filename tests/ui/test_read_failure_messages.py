# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The messages of SPECIFICATION.md §3.6 while running, on the main window."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from gi.repository import Gtk
from ui_helpers import FakeAlertDialog, process_events, type_into

from rature.core import storage
from rature.core.app import App
from rature.core.storage import load
from rature.ui import list_helpers
from rature.ui.application import RatureApplication
from rature.ui.window import RatureWindow


class _Running:
    def __init__(self, window: RatureWindow, app: App) -> None:
        self.window = window
        self.app = app
        self.quits = 0
        self.path: Path = app.data_dir / "data.json"

    @property
    def dialog(self) -> FakeAlertDialog:
        return FakeAlertDialog.shown[-1]

    def gesture(self, text: str = "never written") -> None:
        type_into(self.window.day_view.entry, text)

    def shown(self) -> list[str]:
        rows = list_helpers.rows(self.window.day_view.active_list)
        return [row.text_label.get_label() for row in rows]

    def first_row(self) -> Any:
        return next(iter(list_helpers.rows(self.window.day_view.active_list)))


@pytest.fixture
def running(
    application: RatureApplication,
    window: RatureWindow,
    app: App,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[_Running]:
    FakeAlertDialog._real_class = Gtk.AlertDialog
    FakeAlertDialog.shown = []
    monkeypatch.setattr(Gtk, "AlertDialog", FakeAlertDialog)
    state = _Running(window, app)

    def count() -> None:
        state.quits += 1

    monkeypatch.setattr(application, "quit", count)
    state.gesture("buy bread")
    yield state
    application._failing_window = None


def _refuse(*_args: Any, **_kwargs: Any) -> None:
    raise PermissionError("no access")


def test_a_future_version_alerts_on_the_window_then_quits(running: _Running) -> None:
    raw = json.loads(running.path.read_text())
    raw["version"] += 1
    running.path.write_text(json.dumps(raw))
    before = running.path.read_bytes()

    running.gesture()

    assert running.dialog.get_message() == (
        "This file was saved by a newer version of Rature."
    )
    assert running.dialog.parent is running.window
    assert list(running.dialog.get_buttons()) == ["Quit"]
    running.dialog.press("Quit")
    assert running.quits == 1
    assert running.path.read_bytes() == before


def test_an_unreadable_file_offers_this_devices_data(running: _Running) -> None:
    running.path.write_text("half delivered")

    running.gesture()

    assert running.dialog.get_message() == "The data file cannot be read."
    assert running.dialog.parent is running.window
    assert list(running.dialog.get_buttons()) == [
        "Try Again",
        "Set Aside and Save This Device's Data",
        "Quit",
    ]
    running.dialog.press("Set Aside and Save This Device's Data")
    assert running.dialog.get_message() == "Save this device's data?"
    assert running.path.read_text() == "half delivered"

    running.dialog.press("Save This Device's Data")

    assert [task.text for task in load(data_dir=running.app.data_dir).day.tasks] == [
        "buy bread"
    ]
    (aside,) = running.app.data_dir.glob("data.json.*.bak")
    assert aside.read_text() == "half delivered"
    assert running.shown() == ["buy bread"]
    assert running.quits == 0


def test_a_missing_file_offers_this_devices_data(running: _Running) -> None:
    running.path.unlink()

    running.gesture()

    assert running.dialog.get_message() == "The data file is missing."
    assert str(running.app.data_dir) in running.dialog.get_detail()
    running.dialog.press("Save This Device's Data")
    assert not running.path.exists()
    running.dialog.press("Save This Device's Data")

    assert [task.text for task in load(data_dir=running.app.data_dir).day.tasks] == [
        "buy bread"
    ]


def test_cancelling_the_confirmation_returns_to_the_message(running: _Running) -> None:
    running.path.unlink()
    running.gesture()
    running.dialog.press("Save This Device's Data")

    running.dialog.press("Cancel")

    assert running.dialog.get_message() == "The data file is missing."
    assert not running.path.exists()


def test_quitting_the_message_writes_nothing(running: _Running) -> None:
    running.path.unlink()
    running.gesture()

    running.dialog.press("Quit")

    assert running.quits == 1
    assert not running.path.exists()


def test_escape_on_the_message_tries_again_rather_than_quits(
    running: _Running,
) -> None:
    running.path.unlink()
    running.gesture()
    first = running.dialog

    first.dismiss()

    assert running.quits == 0
    assert running.dialog is not first
    assert running.dialog.get_message() == "The data file is missing."


def test_try_again_shows_a_delivered_file_without_replaying_the_gesture(
    running: _Running,
) -> None:
    content = running.path.read_bytes()
    running.path.write_text("half delivered")
    running.gesture()
    running.path.write_bytes(content)
    App.open(running.app.data_dir, clock=running.app.clock).add("delivered")

    running.dialog.press("Try Again")
    process_events()

    assert running.shown() == ["buy bread", "delivered"]
    assert len(FakeAlertDialog.shown) == 1

    running.gesture("second")
    assert running.shown() == ["buy bread", "delivered", "second"]


def test_a_refused_set_aside_alerts_then_returns_to_the_message(
    running: _Running, monkeypatch: pytest.MonkeyPatch
) -> None:
    running.path.write_text("half delivered")
    monkeypatch.setattr(storage, "set_aside", _refuse)
    running.gesture()
    running.dialog.press("Set Aside and Save This Device's Data")
    running.dialog.press("Save This Device's Data")

    assert running.dialog.get_message() == "Rature could not use its data folder."
    assert list(running.dialog.get_buttons()) == ["Close"]
    running.dialog.press("Close")

    assert running.dialog.get_message() == "The data file cannot be read."
    assert running.quits == 0
    assert running.path.read_text() == "half delivered"


def test_a_failed_write_shows_the_banner_and_the_next_gesture_asks_nothing(
    running: _Running, monkeypatch: pytest.MonkeyPatch
) -> None:
    running.path.unlink()
    running.gesture()
    running.dialog.press("Save This Device's Data")
    with monkeypatch.context() as patch:
        patch.setattr(storage, "save", _refuse)
        running.dialog.press("Save This Device's Data")
        process_events()
    banner = running.window.day_view.banner
    assert banner.get_revealed()
    assert banner.get_title() == "Changes could not be saved to disk."
    shown_so_far = len(FakeAlertDialog.shown)

    running.gesture("next gesture")

    assert len(FakeAlertDialog.shown) == shown_so_far
    assert not banner.get_revealed()
    assert [task.text for task in load(data_dir=running.app.data_dir).day.tasks] == [
        "buy bread",
        "next gesture",
    ]


def test_an_open_rename_does_not_open_a_second_message(running: _Running) -> None:
    row = running.first_row()
    row.rename_button.emit("clicked")
    process_events()
    running.path.unlink()

    type_into(row.rename_entry, "renamed")
    assert len(FakeAlertDialog.shown) == 1

    running.gesture()

    assert len(FakeAlertDialog.shown) == 1


def test_a_rename_never_written_leaves_the_row_once_recovered(
    running: _Running,
) -> None:
    content = running.path.read_bytes()
    row = running.first_row()
    row.rename_button.emit("clicked")
    process_events()
    running.path.unlink()
    type_into(row.rename_entry, "renamed")
    running.path.write_bytes(content)

    running.dialog.press("Try Again")
    process_events()

    assert running.shown() == ["buy bread"]
