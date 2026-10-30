# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Reserve view, driven through its real widgets (SPECIFICATION.md §3.3)."""

from ui_helpers import drop_on_half, process_events, type_into

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
    return drop_on_half(ReserveRow, source, target, upper_half=upper_half)


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


def test_rename_from_the_row_menu_commits_on_enter(
    window: RatureWindow, app: App
) -> None:
    _add(window, "learn the cello")
    row = _rows(window)[0]

    row.rename_button.emit("clicked")
    process_events()
    type_into(row.rename_entry, "learn the viola")

    assert app.session.reserve[0].text == "learn the viola"
    assert row.text_label.get_label() == "learn the viola"


def test_priority_from_the_row_menu_marks_the_item(
    window: RatureWindow, app: App
) -> None:
    _add(window, "learn the cello")

    _rows(window)[0].priority_button.emit("clicked")
    process_events()

    assert app.session.reserve[0].priority
    assert _rows(window)[0].priority_icon.get_child_visible()


def test_delete_from_the_row_menu_removes_the_item(
    window: RatureWindow, app: App
) -> None:
    _add(window, "x", "y")

    _rows(window)[0].delete_button.emit("clicked")
    process_events()

    assert [item.text for item in app.session.reserve] == ["y"]
    assert _texts(window) == ["y"]
