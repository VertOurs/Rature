# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The startup messages of SPECIFICATION.md §3.6, before any window exists.

Gtk.AlertDialog stays real for everything it is told, only its answer is
played here: choose() opens a window on the display that a test cannot click
through broadway.
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from gi.repository import GLib, Gtk
from ui_helpers import process_events

from rature.core import storage
from rature.core.app import App
from rature.ui.application import RatureApplication


class _Dialog:
    """A real Gtk.AlertDialog whose answer comes from the test."""

    shown: list["_Dialog"] = []  # noqa: RUF012
    _real_class: Any = None

    def __init__(self) -> None:
        self._real = _Dialog._real_class()
        self._callback: Callable[[Any, Any], None] | None = None
        self._choice: int | None = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    def choose(self, _parent: Any, _cancellable: Any, callback: Any) -> None:
        self._callback = callback
        _Dialog.shown.append(self)

    def choose_finish(self, _result: Any) -> int:
        if self._choice is None:
            raise GLib.Error("dismissed")
        return self._choice

    def press(self, label: str) -> None:
        self._choice = list(self._real.get_buttons()).index(label)
        self._callback(self, None)

    def dismiss(self) -> None:
        self._callback(self, None)


class _Startup:
    def __init__(self, application: RatureApplication, folder: Path) -> None:
        self.application = application
        self.folder = folder
        self.holds = 0
        self.releases = 0
        self.quits = 0

    @property
    def dialog(self) -> _Dialog:
        return _Dialog.shown[-1]

    def message(self) -> str:
        return self.dialog.get_message()

    def windows(self) -> list[Gtk.Window]:
        return list(self.application.get_windows())


@pytest.fixture
def startup(
    application: RatureApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[_Startup]:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    _Dialog._real_class = Gtk.AlertDialog
    _Dialog.shown = []
    monkeypatch.setattr(Gtk, "AlertDialog", _Dialog)
    state = _Startup(application, tmp_path / "rature")

    def count(name: str) -> Callable[[], None]:
        def counted() -> None:
            setattr(state, name, getattr(state, name) + 1)

        return counted

    monkeypatch.setattr(application, "hold", count("holds"))
    monkeypatch.setattr(application, "release", count("releases"))
    monkeypatch.setattr(application, "quit", count("quits"))
    application._app = None
    application._held_for_dialogs = False
    yield state
    for window in state.windows():
        window.destroy()
    process_events()
    application._app = None
    application._held_for_dialogs = False


def _unreadable(startup: _Startup) -> Path:
    startup.folder.mkdir()
    path = startup.folder / "data.json"
    path.write_text("half delivered", encoding="utf-8")
    return path


def test_a_first_launch_opens_the_window_and_creates_nothing(startup: _Startup) -> None:
    startup.application.do_activate()

    assert _Dialog.shown == []
    assert len(startup.windows()) == 1
    assert not startup.folder.exists()
    assert (startup.holds, startup.quits) == (0, 0)


def test_the_unreadable_file_path_through_every_button(startup: _Startup) -> None:
    path = _unreadable(startup)

    startup.application.do_activate()
    assert startup.message() == "The data file cannot be read."
    assert str(path) in startup.dialog.get_detail()

    startup.dialog.press("Try Again")
    startup.dialog.press("Try Again")
    assert startup.message() == "The data file cannot be read."

    startup.dialog.press("Set Aside and Start Empty")
    assert startup.message() == "Start from an empty day?"
    startup.dialog.press("Cancel")
    assert startup.message() == "The data file cannot be read."

    # Nothing written so far, and no window.
    assert [p.name for p in startup.folder.iterdir()] == ["data.json"]
    assert path.read_text(encoding="utf-8") == "half delivered"
    assert startup.windows() == []
    assert (startup.holds, startup.releases) == (1, 0)

    startup.dialog.press("Set Aside and Start Empty")
    startup.dialog.press("Start Empty")

    assert len(startup.windows()) == 1
    assert (startup.holds, startup.releases, startup.quits) == (1, 1, 0)
    names = sorted(p.name for p in startup.folder.iterdir())
    assert names[0] == "data.json"
    assert names[1].startswith("data.json.") and names[1].endswith(".bak")
    assert (startup.folder / names[1]).read_text(encoding="utf-8") == "half delivered"
    assert storage.load(data_dir=startup.folder).day.tasks == []


def test_the_missing_file_path_through_every_button(startup: _Startup) -> None:
    startup.folder.mkdir()

    startup.application.do_activate()
    assert startup.message() == "The data file is missing."
    assert str(startup.folder) in startup.dialog.get_detail()

    startup.dialog.press("Try Again")
    startup.dialog.press("Try Again")
    startup.dialog.press("Start Empty")
    assert startup.message() == "Start from an empty day?"
    startup.dialog.press("Cancel")
    assert startup.message() == "The data file is missing."
    assert list(startup.folder.iterdir()) == []

    startup.dialog.press("Start Empty")
    startup.dialog.press("Start Empty")

    assert len(startup.windows()) == 1
    assert (startup.holds, startup.releases) == (1, 1)
    assert [p.name for p in startup.folder.iterdir()] == ["data.json"]


def test_try_again_finds_a_file_delivered_in_the_meantime(startup: _Startup) -> None:
    path = _unreadable(startup)
    startup.application.do_activate()

    App.open(startup.folder.parent / "elsewhere").add("delivered")
    delivered = (startup.folder.parent / "elsewhere" / "data.json").read_bytes()
    path.write_bytes(delivered)
    startup.dialog.press("Try Again")

    assert len(startup.windows()) == 1
    assert (startup.holds, startup.releases) == (1, 1)
    assert path.read_bytes() == delivered


@pytest.mark.parametrize("leave", ["press", "dismiss"])
def test_leaving_the_message_quits_without_writing(
    startup: _Startup, leave: str
) -> None:
    path = _unreadable(startup)
    startup.application.do_activate()

    if leave == "press":
        startup.dialog.press("Quit")
    else:
        startup.dialog.dismiss()

    assert startup.windows() == []
    assert (startup.holds, startup.releases, startup.quits) == (1, 1, 1)
    assert path.read_text(encoding="utf-8") == "half delivered"


def test_dismissing_the_confirmation_is_a_cancel(startup: _Startup) -> None:
    _unreadable(startup)
    startup.application.do_activate()
    startup.dialog.press("Set Aside and Start Empty")

    startup.dialog.dismiss()

    assert startup.message() == "The data file cannot be read."
    assert startup.quits == 0


def test_a_second_activation_does_not_start_a_second_loop(startup: _Startup) -> None:
    _unreadable(startup)
    startup.application.do_activate()
    startup.application.do_activate()

    assert len(_Dialog.shown) == 1
    assert startup.holds == 1


def test_a_refused_set_aside_alerts_then_quits(
    startup: _Startup, monkeypatch: pytest.MonkeyPatch
) -> None:
    # §3.6 situation 4, under the same single hold.
    path = _unreadable(startup)

    def refuse(*_args: Any, **_kwargs: Any) -> None:
        raise PermissionError("no access")

    monkeypatch.setattr(storage, "set_aside", refuse)
    startup.application.do_activate()
    startup.dialog.press("Set Aside and Start Empty")
    startup.dialog.press("Start Empty")

    assert startup.message() == "Rature could not use its data folder."
    assert startup.holds == 1
    startup.dialog.press("Quit")
    assert (startup.releases, startup.quits) == (1, 1)
    assert path.exists()


def test_a_failed_write_of_the_empty_day_opens_the_window_with_the_banner(
    startup: _Startup, monkeypatch: pytest.MonkeyPatch
) -> None:
    # §3.6 situation 3: the application stays usable.
    startup.folder.mkdir()

    def refuse(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(storage, "save", refuse)
    startup.application.do_activate()
    startup.dialog.press("Start Empty")
    startup.dialog.press("Start Empty")
    process_events()

    (window,) = startup.windows()
    assert window.day_view.banner.get_revealed()
    assert startup.quits == 0
