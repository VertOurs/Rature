# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Real widgets under gtk4-broadwayd, on the installed application.

Run by build-aux/ui-tests.sh inside the GNOME SDK, which installs Rature
into a scratch prefix and exports RATURE_UI_PREFIX. Anywhere else (no gi,
or no installed copy) the whole directory is skipped: the pure-Python
suite stays runnable on an interpreter without PyGObject (ADR 0002).
"""

import os
import sys
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("gi", reason="UI tests need PyGObject")
if "RATURE_UI_PREFIX" not in os.environ:
    pytest.skip("UI tests run through build-aux/ui-tests.sh", allow_module_level=True)

_PKGDATADIR = Path(os.environ["RATURE_UI_PREFIX"]) / "share" / "rature"
# The installed package, not src/: it is what ships, generated config.py
# and compiled resources included.
sys.path.insert(0, str(_PKGDATADIR))

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio  # noqa: E402

Gio.resources_register(Gio.Resource.load(str(_PKGDATADIR / "rature.gresource")))
Adw.init()

from ui_helpers import process_events  # noqa: E402

from rature.core.app import App  # noqa: E402
from rature.ui.application import RatureApplication  # noqa: E402
from rature.ui.window import RatureWindow  # noqa: E402

PARIS = timezone(timedelta(hours=2))


@pytest.fixture
def now() -> list[datetime]:
    """The clock's current time, in a list so a test can move it."""
    return [datetime(2026, 8, 24, 10, 0, tzinfo=PARIS)]


@pytest.fixture
def app(tmp_path: Path, now: list[datetime]) -> App:
    clock: Callable[[], datetime] = lambda: now[0]  # noqa: E731
    return App.open(tmp_path / "rature", clock=clock)


@pytest.fixture(scope="session")
def application() -> RatureApplication:
    """The real application, registered once: its startup loads the CSS.

    Non-unique, so a Rature already running on the machine is never asked
    to open the window instead. Never run(): the tests drive the main loop.
    """
    rature = RatureApplication()
    rature.set_flags(Gio.ApplicationFlags.NON_UNIQUE)
    rature.register(None)
    return rature


@pytest.fixture
def window(application: RatureApplication, app: App) -> Iterator[RatureWindow]:
    main_window = RatureWindow(application=application, app=app)
    main_window.present()
    process_events()
    yield main_window
    main_window.destroy()
    process_events()
