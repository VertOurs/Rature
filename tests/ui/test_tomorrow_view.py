# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Tomorrow view's prepared tasks, driven through their real widgets.

SPECIFICATION.md §3.16. Recurring templates due tomorrow are read-only
rows, not covered here.
"""

from ui_helpers import drop_on_half, process_events, type_into

from rature.core.app import App
from rature.ui import list_helpers
from rature.ui.prepared_row import PreparedRow
from rature.ui.window import RatureWindow


def _rows(window: RatureWindow) -> list[PreparedRow]:
    return list(list_helpers.rows(window.tomorrow_view.prepared_list))


def _texts(window: RatureWindow) -> list[str]:
    return [row.task.text for row in _rows(window)]


def _add(window: RatureWindow, *texts: str) -> None:
    # Shown first: a hidden view is never laid out, and a drop needs the
    # row's height.
    window.activate_action("win.view-tomorrow")
    for text in texts:
        type_into(window.tomorrow_view.entry, text)


def _drop(source: PreparedRow, target: PreparedRow, *, upper_half: bool) -> bool:
    return drop_on_half(PreparedRow, source, target, upper_half=upper_half)


def test_enter_in_the_entry_prepares_a_task(window: RatureWindow, app: App) -> None:
    _add(window, "book the train")

    assert [task.text for task in app.session.tomorrow] == ["book the train"]
    assert _texts(window) == ["book the train"]


def test_rename_from_the_row_menu_commits_on_enter(
    window: RatureWindow, app: App
) -> None:
    _add(window, "book the train")
    row = _rows(window)[0]

    row.rename_button.emit("clicked")
    process_events()
    type_into(row.rename_entry, "book the night train")

    assert app.session.tomorrow[0].text == "book the night train"
    assert row.text_label.get_label() == "book the night train"


def test_priority_from_the_row_menu_marks_the_task(
    window: RatureWindow, app: App
) -> None:
    _add(window, "book the train")

    _rows(window)[0].priority_button.emit("clicked")
    process_events()

    assert app.session.tomorrow[0].priority
    assert _rows(window)[0].priority_icon.get_child_visible()


def test_delete_from_the_row_menu_removes_the_task(
    window: RatureWindow, app: App
) -> None:
    _add(window, "book the train", "pack")

    _rows(window)[0].delete_button.emit("clicked")
    process_events()

    assert [task.text for task in app.session.tomorrow] == ["pack"]
    assert _texts(window) == ["pack"]


def test_dropping_on_the_upper_half_of_a_task_moves_before_it(
    window: RatureWindow, app: App
) -> None:
    _add(window, "x", "y", "z")
    first, _, last = _rows(window)

    assert _drop(last, first, upper_half=True)

    assert [task.text for task in app.session.tomorrow] == ["z", "x", "y"]
    assert _texts(window) == ["z", "x", "y"]


def test_a_task_dropped_on_itself_is_refused(window: RatureWindow, app: App) -> None:
    _add(window, "x", "y")
    first = _rows(window)[0]

    assert not _drop(first, first, upper_half=True)

    assert [task.text for task in app.session.tomorrow] == ["x", "y"]
