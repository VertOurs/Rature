# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The return of focus of SPECIFICATION.md §3.1, and the case of ADR 0007.

Under broadway nothing takes the focus away, so the tests play the signal.
"""

from datetime import datetime, timedelta
from typing import Any

import pytest
from gi.repository import Gtk
from ui_helpers import FakeAlertDialog, process_events, type_into, wait_for_layout

from rature.core.app import App
from rature.ui import list_helpers
from rature.ui.archives_window import ArchivesWindow
from rature.ui.statistics_window import StatisticsWindow
from rature.ui.window import RatureWindow


def _regain_focus(window: RatureWindow, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(window, "is_active", lambda: True)
    window.notify("is-active")
    process_events()


def _add(window: RatureWindow, *texts: str) -> None:
    for text in texts:
        type_into(window.day_view.entry, text)


def _rows(window: RatureWindow) -> list[Any]:
    return list(list_helpers.rows(window.day_view.active_list))


def _texts(window: RatureWindow) -> list[str]:
    return [row.text_label.get_label() for row in _rows(window)]


def _other_device_adds(app: App) -> None:
    App.open(app.data_dir, clock=app.clock).add("from the other device")


def test_a_changed_file_shows_on_return_of_focus(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    _add(window, "buy bread")
    _other_device_adds(app)

    _regain_focus(window, monkeypatch)

    assert _texts(window) == ["buy bread", "from the other device"]


def test_an_unchanged_file_rebuilds_nothing(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    _add(window, "buy bread")
    row = _rows(window)[0]
    session = app.session

    _regain_focus(window, monkeypatch)

    assert _rows(window)[0] is row
    assert app.session is session


def test_losing_the_focus_reads_nothing(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    _add(window, "buy bread")
    _other_device_adds(app)
    monkeypatch.setattr(window, "is_active", lambda: False)

    window.notify("is-active")
    process_events()

    assert _texts(window) == ["buy bread"]


def test_an_open_menu_keeps_its_row_until_it_closes(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    # ADR 0007, "Withdrawal": the row was destroyed under its open menu, and
    # Rename and Delete had no effect any more.
    _add(window, "buy bread")
    row = _rows(window)[0]
    row.row_popover.popup()
    process_events()
    session = app.session
    _other_device_adds(app)

    _regain_focus(window, monkeypatch)

    assert _rows(window)[0] is row
    assert app.session is session
    assert row.row_popover.get_visible()

    row.row_popover.popdown()
    process_events()

    assert _texts(window) == ["buy bread", "from the other device"]


def test_rename_chosen_from_the_menu_keeps_the_entry_open(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Rename closes the menu before it opens the entry: the waiting reload
    # must not destroy the row in between.
    _add(window, "buy bread")
    row = _rows(window)[0]
    row.row_popover.popup()
    process_events()
    _other_device_adds(app)
    _regain_focus(window, monkeypatch)

    row.rename_button.emit("clicked")
    process_events()

    assert _rows(window)[0] is row
    assert row.rename_entry.get_visible()

    type_into(row.rename_entry, "buy rye bread")
    process_events()

    assert _texts(window) == ["buy rye bread", "from the other device"]


def test_an_open_rename_waits_until_it_is_cancelled(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    _add(window, "buy bread")
    row = _rows(window)[0]
    row.rename_button.emit("clicked")
    process_events()
    _other_device_adds(app)

    _regain_focus(window, monkeypatch)
    assert _rows(window)[0] is row
    assert row.rename_entry.get_visible()

    row._rename._cancel()
    process_events()

    assert _texts(window) == ["buy bread", "from the other device"]


def test_a_timer_tick_without_a_rollover_rebuilds_nothing(
    window: RatureWindow, app: App
) -> None:
    # A rebuild every minute would destroy a row mid-drag (ADR 0007).
    _add(window, "buy bread")
    app.add_to_reserve("an item")
    app.add_to_tomorrow("a task")
    app.add_recurring("a template", [0])
    window._refresh_all()
    process_events()
    rows = [
        _rows(window)[0],
        next(iter(list_helpers.rows(window.reserve_view.item_list))),
        next(iter(list_helpers.rows(window.tomorrow_view.prepared_list))),
        next(iter(list_helpers.rows(window.recurring_view.item_list))),
    ]

    window._on_ensure_day_tick()
    process_events()

    assert rows == [
        _rows(window)[0],
        next(iter(list_helpers.rows(window.reserve_view.item_list))),
        next(iter(list_helpers.rows(window.tomorrow_view.prepared_list))),
        next(iter(list_helpers.rows(window.recurring_view.item_list))),
    ]


def test_a_rollover_due_under_an_open_menu_arrives_when_it_closes(
    window: RatureWindow, app: App, now: list[datetime]
) -> None:
    _add(window, "buy bread")
    row = _rows(window)[0]
    row.row_popover.popup()
    process_events()
    today = app.session.day.date
    now[0] += timedelta(days=1)

    window._on_ensure_day_tick()
    process_events()

    assert _rows(window)[0] is row
    assert app.session.day.date == today

    row.row_popover.popdown()
    process_events()

    assert app.session.day.date > today
    assert window.day_view.banner.get_title() == "A new day has started."
    assert window.day_view.banner.get_revealed()


def test_a_rollover_on_return_of_focus_writes_nothing_and_rebuilds(
    window: RatureWindow, app: App, now: list[datetime], monkeypatch
) -> None:
    _add(window, "buy bread")
    before = (app.data_dir / "data.json").read_bytes()
    now[0] += timedelta(days=1)

    _regain_focus(window, monkeypatch)

    assert _texts(window) == []
    assert window.day_view.banner.get_revealed()
    assert (app.data_dir / "data.json").read_bytes() == before


@pytest.mark.parametrize(
    ("view_name", "add"),
    [
        ("reserve_view", lambda app: app.add_to_reserve("an item")),
        ("tomorrow_view", lambda app: app.add_to_tomorrow("a task")),
        ("recurring_view", lambda app: app.add_recurring("a template", [0])),
    ],
)
def test_the_other_views_menus_put_the_reload_off_too(
    window: RatureWindow, app: App, monkeypatch, view_name: str, add: Any
) -> None:
    add(app)
    window._refresh_all()
    process_events()
    view = getattr(window, view_name)
    box = view.prepared_list if view_name == "tomorrow_view" else view.item_list
    sidebar_row = getattr(window, view_name.replace("_view", "_sidebar_row"))
    window.sidebar_list.select_row(sidebar_row)
    row = next(iter(list_helpers.rows(box)))
    wait_for_layout(row)  # a menu only opens on a row that is on screen
    row.row_popover.popup()
    process_events()
    session = app.session
    _other_device_adds(app)

    _regain_focus(window, monkeypatch)

    assert app.session is session
    assert next(iter(list_helpers.rows(box))) is row

    row.row_popover.popdown()
    process_events()

    assert "from the other device" in _texts(window)


def test_a_later_day_from_the_other_device_reaches_the_open_windows(
    window: RatureWindow, app: App, now: list[datetime], monkeypatch
) -> None:
    _add(window, "buy bread")
    archives = ArchivesWindow(app=app, application=window.get_application())
    statistics = StatisticsWindow(app=app, application=window.get_application())
    archives.present()
    statistics.present()
    process_events()
    statistics_refreshes = []
    monkeypatch.setattr(statistics, "refresh", lambda: statistics_refreshes.append(1))
    monday = app.session.day.date
    tomorrow = now[0] + timedelta(days=1)
    App.open(app.data_dir, clock=lambda: tomorrow).add("from the other device")

    _regain_focus(window, monkeypatch)

    assert archives._dates == [monday]
    assert statistics_refreshes == [1]
    archives.destroy()
    statistics.destroy()


def test_a_permission_error_stays_in_the_log(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    _add(window, "buy bread")

    def refuse() -> None:
        raise PermissionError("no access")

    monkeypatch.setattr(app, "catch_up", refuse)
    _regain_focus(window, monkeypatch)

    assert not window.day_view.banner.get_revealed()


def test_a_message_already_open_does_not_open_a_second_one(
    window: RatureWindow, app: App, monkeypatch: pytest.MonkeyPatch
) -> None:
    FakeAlertDialog._real_class = Gtk.AlertDialog
    FakeAlertDialog.shown = []
    monkeypatch.setattr(Gtk, "AlertDialog", FakeAlertDialog)
    _add(window, "buy bread")
    (app.data_dir / "data.json").write_text("half delivered")

    _regain_focus(window, monkeypatch)
    assert FakeAlertDialog.shown[-1].get_message() == "The data file cannot be read."
    _regain_focus(window, monkeypatch)

    assert len(FakeAlertDialog.shown) == 1
    window.get_application()._failing_window = None
