# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Day view, driven through its real widgets (SPECIFICATION.md §3.2)."""

from ui_helpers import process_events

from rature.core.app import App
from rature.ui import list_helpers
from rature.ui.window import RatureWindow


def _row_texts(window: RatureWindow) -> list[str]:
    return [row.task.text for row in list_helpers.rows(window.day_view.active_list)]


def test_enter_in_the_entry_adds_a_task(window: RatureWindow, app: App) -> None:
    entry = window.day_view.entry

    entry.set_text("buy bread")
    entry.emit("activate")
    process_events()

    assert [task.text for task in app.session.day.tasks] == ["buy bread"]
    assert _row_texts(window) == ["buy bread"]
    assert window.day_view.stack.get_visible_child_name() == "tasks"
    # SPECIFICATION.md §3.2: the entry empties and keeps focus, so the next
    # task can be dictated straight away.
    assert entry.get_text() == ""
    assert window.get_focus() is not None
    assert window.get_focus().is_ancestor(entry)
