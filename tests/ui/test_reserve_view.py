# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Reserve view, driven through its real widgets (SPECIFICATION.md §3.3)."""

from gi.repository import GObject
from ui_helpers import drop, type_into

from rature.core.app import App
from rature.ui import list_helpers
from rature.ui.reserve_row import ReserveRow
from rature.ui.window import RatureWindow


def _rows(window: RatureWindow) -> list[ReserveRow]:
    return list(list_helpers.rows(window.reserve_view.item_list))


def _texts(window: RatureWindow) -> list[str]:
    return [row.item.text for row in _rows(window)]


def _add(window: RatureWindow, *texts: str) -> None:
    # Shown first, as a user would see it: a hidden view is never laid
    # out, and a drop needs the row's height.
    window.activate_action("win.view-reserve")
    for text in texts:
        type_into(window.reserve_view.entry, text)


def _drop(source: ReserveRow, target: ReserveRow, *, upper_half: bool) -> bool:
    # The reserve drags the item id as a string (reserve_row.py).
    value = GObject.Value(GObject.TYPE_STRING, source.item.id)
    return drop(ReserveRow, source, target, value, upper_half=upper_half)


def test_enter_in_the_entry_adds_an_item(window: RatureWindow, app: App) -> None:
    _add(window, "learn the cello")

    assert [item.text for item in app.session.reserve] == ["learn the cello"]
    assert _texts(window) == ["learn the cello"]


def test_dropping_on_the_upper_half_of_an_item_moves_before_it(
    window: RatureWindow, app: App
) -> None:
    _add(window, "x", "y", "z")
    first, _, last = _rows(window)

    assert _drop(last, first, upper_half=True)

    assert [item.text for item in app.session.reserve] == ["z", "x", "y"]
    assert _texts(window) == ["z", "x", "y"]


def test_an_item_dropped_on_itself_is_refused(window: RatureWindow, app: App) -> None:
    _add(window, "x", "y")
    first = _rows(window)[0]

    assert not _drop(first, first, upper_half=True)

    assert [item.text for item in app.session.reserve] == ["x", "y"]
