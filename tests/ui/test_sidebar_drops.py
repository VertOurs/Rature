# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Rows dropped on the sidebar entries (SPECIFICATION.md §3.2, §3.3, §3.16).

Each drop carries the source row's real payload: the task row itself for
the Day and Tomorrow rows, the item id for a reserve row. The sidebar's
accept handlers need a GdkDrop, which no test can build; they stay
covered by the visual checks.
"""

from ui_helpers import drop, type_into

from rature.core.app import App
from rature.ui import list_helpers
from rature.ui.prepared_row import PreparedRow
from rature.ui.reserve_row import ReserveRow
from rature.ui.task_row import TaskRow
from rature.ui.window import RatureWindow


def _day_row(window: RatureWindow, text: str) -> TaskRow:
    type_into(window.day_view.entry, text)
    return list(list_helpers.rows(window.day_view.active_list))[-1]


def _reserve_row(window: RatureWindow, text: str) -> ReserveRow:
    type_into(window.reserve_view.entry, text)
    return list(list_helpers.rows(window.reserve_view.item_list))[-1]


def _prepared_row(window: RatureWindow, text: str) -> PreparedRow:
    type_into(window.tomorrow_view.entry, text)
    return list(list_helpers.rows(window.tomorrow_view.prepared_list))[-1]


def test_a_day_task_dropped_on_reserve_goes_back_to_the_reserve(
    window: RatureWindow, app: App
) -> None:
    row = _day_row(window, "buy bread")

    assert drop(TaskRow, row, window.reserve_sidebar_row, y=0.0)

    assert app.session.day.tasks == []
    assert [item.text for item in app.session.reserve] == ["buy bread"]


def test_a_reserve_item_dropped_on_day_is_drawn(window: RatureWindow, app: App) -> None:
    row = _reserve_row(window, "learn the cello")

    assert drop(ReserveRow, row, window.day_sidebar_row, y=0.0)

    assert app.session.reserve == []
    assert [task.text for task in app.session.day.tasks] == ["learn the cello"]


def test_a_day_task_dropped_on_tomorrow_moves_there(
    window: RatureWindow, app: App
) -> None:
    row = _day_row(window, "book the train")

    assert drop(TaskRow, row, window.tomorrow_sidebar_row, y=0.0)

    assert app.session.day.tasks == []
    assert [task.text for task in app.session.tomorrow] == ["book the train"]


def test_a_reserve_item_dropped_on_tomorrow_moves_there(
    window: RatureWindow, app: App
) -> None:
    row = _reserve_row(window, "learn the cello")

    assert drop(ReserveRow, row, window.tomorrow_sidebar_row, y=0.0)

    assert app.session.reserve == []
    assert [task.text for task in app.session.tomorrow] == ["learn the cello"]


def test_a_prepared_task_dropped_on_day_moves_to_today(
    window: RatureWindow, app: App
) -> None:
    row = _prepared_row(window, "pack")

    assert drop(PreparedRow, row, window.day_sidebar_row, y=0.0)

    assert app.session.tomorrow == []
    assert [task.text for task in app.session.day.tasks] == ["pack"]


def test_a_prepared_task_dropped_on_reserve_goes_to_the_reserve(
    window: RatureWindow, app: App
) -> None:
    row = _prepared_row(window, "pack")

    assert drop(PreparedRow, row, window.reserve_sidebar_row, y=0.0)

    assert app.session.tomorrow == []
    assert [item.text for item in app.session.reserve] == ["pack"]
