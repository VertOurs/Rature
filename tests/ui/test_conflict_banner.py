# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The conflict message on the one banner, SPECIFICATION.md §3.6 and §3.17."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from gi.repository import Gio, GLib, Gtk
from ui_helpers import process_events, type_into

from rature.core import storage
from rature.core.app import App
from rature.ui.window import RatureWindow

_CONFLICT = "Two devices changed the data at the same time. Both versions were kept."
_NEW_DAY = "A new day has started."
_WRITE_FAILURE = "Changes could not be saved to disk."


def _copy(app: App) -> Path:
    return app.data_dir / "data.sync-conflict-20260824-100000-ABCDEFG.json"


def _regain_focus(window: RatureWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(window, "is_active", lambda: True)
    window.notify("is-active")
    process_events()


@pytest.fixture
def conflict(window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A conflict copy on disk, seen by the window."""
    type_into(window.day_view.entry, "buy bread")
    copy = _copy(app)
    copy.write_text("{}")
    _regain_focus(window, monkeypatch)
    return copy


def test_a_copy_shows_the_banner_with_its_button(
    window: RatureWindow, conflict: Path
) -> None:
    banner = window.day_view.banner
    assert banner.get_revealed()
    assert banner.get_title() == _CONFLICT
    assert banner.get_button_label() == "Open Folder"


def test_the_banner_goes_when_no_copy_remains(
    window: RatureWindow, conflict: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    conflict.unlink()

    _regain_focus(window, monkeypatch)

    assert not window.day_view.banner.get_revealed()


def test_the_button_opens_the_folder_and_keeps_the_banner(
    window: RatureWindow, conflict: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[bool] = []
    monkeypatch.setattr(window, "_open_data_folder", lambda: opened.append(True))

    window.day_view.banner.emit("button-clicked")

    assert opened == [True]
    assert window.day_view.banner.get_title() == _CONFLICT
    assert window.day_view.banner.get_revealed()
    assert conflict.exists()


def test_the_folder_opened_is_the_data_folder(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    launched: list[Any] = []

    class FakeLauncher:
        @staticmethod
        def new(file: Gio.File) -> "FakeLauncher":
            launched.append(file.get_path())
            return FakeLauncher()

        def launch(self, parent: Any, _cancellable: Any, _callback: Any) -> None:
            launched.append(parent)

    monkeypatch.setattr(Gtk, "FileLauncher", FakeLauncher)

    window._open_data_folder()

    assert launched == [str(app.data_dir), window]


def test_a_failed_launch_only_goes_to_the_log(
    window: RatureWindow, caplog: pytest.LogCaptureFixture
) -> None:
    class RefusingLauncher:
        def launch_finish(self, _result: Any) -> None:
            raise GLib.Error("no file manager")

    window._on_data_folder_opened(RefusingLauncher(), None)

    assert "could not open the data folder" in caplog.text


def test_a_write_failure_hides_the_conflict_until_the_next_write(
    window: RatureWindow, conflict: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    banner = window.day_view.banner
    real_save = storage.save

    def refuse(*_args: object, **_kwargs: object) -> str:
        raise OSError

    monkeypatch.setattr(storage, "save", refuse)
    type_into(window.day_view.entry, "buy milk")
    process_events()
    assert banner.get_title() == _WRITE_FAILURE
    assert banner.get_button_label() in (None, "")

    monkeypatch.setattr(storage, "save", real_save)
    type_into(window.day_view.entry, "buy eggs")
    process_events()
    assert banner.get_title() == _CONFLICT


def test_the_conflict_hides_the_new_day_until_it_is_gone(
    window: RatureWindow,
    conflict: Path,
    now: list[datetime],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    banner = window.day_view.banner
    now[0] += timedelta(days=1)
    window._on_ensure_day_tick()
    process_events()
    assert banner.get_title() == _CONFLICT

    conflict.unlink()
    _regain_focus(window, monkeypatch)

    assert banner.get_title() == _NEW_DAY
    assert banner.get_button_label() == "Dismiss"


def test_a_dismissed_new_day_stays_away_under_a_new_conflict(
    window: RatureWindow,
    app: App,
    now: list[datetime],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    banner = window.day_view.banner
    now[0] += timedelta(days=1)
    window._on_ensure_day_tick()
    process_events()
    banner.emit("button-clicked")
    assert not banner.get_revealed()

    copy = _copy(app)
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_text("{}")
    _regain_focus(window, monkeypatch)
    assert banner.get_title() == _CONFLICT

    copy.unlink()
    _regain_focus(window, monkeypatch)
    assert not banner.get_revealed()
