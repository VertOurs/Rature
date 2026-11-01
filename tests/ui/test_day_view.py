# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Day view, driven through its real widgets (SPECIFICATION.md §3.2)."""

from datetime import date, datetime, timedelta

from ui_helpers import drop_on_half, process_events, type_into

from rature.core.app import App
from rature.ui import list_helpers
from rature.ui.archives_window import ArchivesWindow
from rature.ui.task_row import TaskRow
from rature.ui.window import RatureWindow


def _rows(list_box) -> list[TaskRow]:
    return list(list_helpers.rows(list_box))


def _active(window: RatureWindow) -> list[TaskRow]:
    return _rows(window.day_view.active_list)


def _struck(window: RatureWindow) -> list[TaskRow]:
    return _rows(window.day_view.struck_list)


def _texts(rows: list[TaskRow]) -> list[str]:
    return [row.task.text for row in rows]


def _add(window: RatureWindow, *texts: str) -> None:
    for text in texts:
        type_into(window.day_view.entry, text)


def _drop(source: TaskRow, target: TaskRow, *, upper_half: bool) -> bool:
    return drop_on_half(TaskRow, source, target, upper_half=upper_half)


def test_enter_in_the_entry_adds_a_task(window: RatureWindow, app: App) -> None:
    entry = window.day_view.entry

    _add(window, "buy bread")

    assert [task.text for task in app.session.day.tasks] == ["buy bread"]
    assert _texts(_active(window)) == ["buy bread"]
    assert window.day_view.stack.get_visible_child_name() == "tasks"
    # SPECIFICATION.md §3.2: the entry empties and keeps focus, so the next
    # task can be dictated straight away.
    assert entry.get_text() == ""
    assert window.get_focus() is not None
    assert window.get_focus().is_ancestor(entry)


def test_the_strike_button_moves_the_task_to_the_struck_block(
    window: RatureWindow, app: App
) -> None:
    _add(window, "buy bread", "call the dentist")

    _active(window)[0].strike_button.emit("clicked")
    process_events()

    assert [task.done for task in app.session.day.tasks] == [True, False]
    (struck,) = _struck(window)
    assert struck.task.text == "buy bread"
    assert struck.text_label.has_css_class("rature-struck")
    assert _texts(_active(window)) == ["call the dentist"]


def test_the_strike_button_on_a_struck_task_undoes_the_strike(
    window: RatureWindow, app: App
) -> None:
    _add(window, "buy bread")
    _active(window)[0].strike_button.emit("clicked")
    process_events()

    _struck(window)[0].strike_button.emit("clicked")
    process_events()

    assert not app.session.day.tasks[0].done
    assert _struck(window) == []
    assert _texts(_active(window)) == ["buy bread"]


def test_rename_from_the_row_menu_commits_on_enter(
    window: RatureWindow, app: App
) -> None:
    _add(window, "buy bread")
    row = _active(window)[0]

    row.rename_button.emit("clicked")
    process_events()
    assert row.rename_entry.get_visible()
    assert row.rename_entry.get_text() == "buy bread"
    type_into(row.rename_entry, "buy rye bread")

    assert app.session.day.tasks[0].text == "buy rye bread"
    assert not row.rename_entry.get_visible()
    assert row.text_label.get_label() == "buy rye bread"
    # SPECIFICATION.md §2.4: a rename keeps the number.
    assert app.session.day.tasks[0].num == 1


def test_dropping_on_the_upper_half_of_a_row_moves_before_it(
    window: RatureWindow, app: App
) -> None:
    _add(window, "a", "b", "c")
    first, _, last = _active(window)

    assert _drop(last, first, upper_half=True)

    assert [task.text for task in app.session.day.tasks] == ["c", "a", "b"]
    assert _texts(_active(window)) == ["c", "a", "b"]
    # SPECIFICATION.md §2.4: numbers are labels, a reorder never renumbers.
    assert [row.task.num for row in _active(window)] == [3, 1, 2]


def test_dropping_on_the_lower_half_of_a_row_moves_after_it(
    window: RatureWindow, app: App
) -> None:
    _add(window, "a", "b", "c")
    first, middle, _ = _active(window)

    assert _drop(first, middle, upper_half=False)

    assert _texts(_active(window)) == ["b", "a", "c"]


def test_a_drop_onto_the_other_block_is_refused(window: RatureWindow, app: App) -> None:
    _add(window, "a", "b")
    _active(window)[0].strike_button.emit("clicked")
    process_events()

    assert not _drop(_active(window)[0], _struck(window)[0], upper_half=True)

    assert [task.text for task in app.session.day.tasks] == ["a", "b"]


def test_priority_from_the_row_menu_marks_the_task(
    window: RatureWindow, app: App
) -> None:
    _add(window, "buy bread")

    _active(window)[0].priority_button.emit("clicked")
    process_events()

    assert app.session.day.tasks[0].priority
    assert _active(window)[0].priority_icon.get_child_visible()


def test_delete_from_the_row_menu_removes_the_task_and_can_be_undone(
    window: RatureWindow, app: App
) -> None:
    _add(window, "buy bread", "call the dentist")

    _active(window)[0].delete_button.emit("clicked")
    process_events()

    assert _texts(_active(window)) == ["call the dentist"]
    # SPECIFICATION.md §2.2: Delete goes to the journal, so Undo exists.
    assert [entry.text for entry in app.session.day.deletions] == ["buy bread"]


def test_undo_restores_the_task_and_then_turns_insensitive(
    window: RatureWindow, app: App
) -> None:
    _add(window, "buy bread")
    undo = window.lookup_action("undo-delete")
    assert not undo.get_enabled()

    _active(window)[0].delete_button.emit("clicked")
    process_events()
    assert undo.get_enabled()

    undo.activate(None)
    process_events()
    assert _texts(_active(window)) == ["buy bread"]
    assert not undo.get_enabled()


def test_undo_turns_insensitive_when_the_timer_rolls_the_day_over(
    window: RatureWindow, app: App, now: list[datetime]
) -> None:
    # SPECIFICATION.md §3.2: a deletion made before 04:00 leaves the button
    # active on an empty journal otherwise, and a click would raise KeyError.
    _add(window, "buy bread")
    _active(window)[0].delete_button.emit("clicked")
    process_events()
    undo = window.lookup_action("undo-delete")
    assert undo.get_enabled()

    now[0] += timedelta(days=1)
    window._on_ensure_day_tick()
    process_events()

    assert not undo.get_enabled()


def test_the_timer_announces_a_new_day_without_touching_the_archives_window(
    window: RatureWindow, app: App, now: list[datetime]
) -> None:
    _add(window, "buy bread")
    archives = ArchivesWindow(app=app, application=window.get_application())
    archives.present()
    process_events()

    now[0] += timedelta(days=1)
    window._on_ensure_day_tick()
    process_events()

    banner = window.day_view.banner
    assert banner.get_revealed()
    assert banner.get_title() == "A new day has started."
    assert archives._dates == []
    archives.destroy()


def test_the_first_gesture_refreshes_the_archives_window(
    window: RatureWindow, app: App, now: list[datetime]
) -> None:
    _add(window, "buy bread")
    archives = ArchivesWindow(app=app, application=window.get_application())
    archives.present()
    process_events()
    now[0] += timedelta(days=1)
    window._on_ensure_day_tick()
    process_events()

    _add(window, "first gesture")
    process_events()

    assert archives._dates == [date(2026, 8, 24)]
    archives.destroy()
