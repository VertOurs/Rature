# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Task and reserve priority: SPECIFICATION.md §2.5 and §2.7.8."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core.app import App
from rature.core.models import Deletion, Origin, ReserveItem, Task
from rature.core.session import Day, Session

PARIS = timezone(timedelta(hours=2))
D24 = date(2026, 8, 24)
NOW = datetime(2026, 8, 24, 14, 0, tzinfo=PARIS)
NEXT_DAY = datetime(2026, 8, 25, 9, 0, tzinfo=PARIS)


def make_session() -> Session:
    return Session(Day(date=D24))


def snapshot(session: Session) -> list[tuple[str, int]]:
    return [(task.id, task.num) for task in session.view()]


# The models carry it, false by default.


def test_priority_round_trips_on_every_model() -> None:
    task = Task(num=1, text="call", origin=Origin.DAY, priority=True)
    item = ReserveItem(text="fix the bike", created=D24, priority=True)
    entry = Deletion(
        id="t1",
        num=1,
        text="call",
        origin=Origin.DAY,
        deleted_at=NOW,
        index=0,
        priority=True,
    )
    assert Task.from_dict(task.to_dict()) == task
    assert ReserveItem.from_dict(item.to_dict()) == item
    assert Deletion.from_dict(entry.to_dict()) == entry


def test_priority_is_off_by_default() -> None:
    assert not Task(num=1, text="call", origin=Origin.DAY).priority
    assert not ReserveItem(text="fix the bike", created=D24).priority


# Marking changes neither the order nor the numbers (7.2 end criterion).


def test_marking_a_task_keeps_the_order_and_the_numbers() -> None:
    session = make_session()
    first = session.add("first")
    second = session.add("second")
    third = session.add("third")
    session.strike(third.id, now=NOW)
    before = snapshot(session)
    session.set_priority(second.id, priority=True)
    session.set_priority(third.id, priority=True)
    assert snapshot(session) == before
    assert session.day.counter == 4
    session.set_priority(second.id, priority=False)
    assert snapshot(session) == before
    assert (first.priority, second.priority, third.priority) == (False, False, True)


def test_marking_a_reserve_item_keeps_the_order() -> None:
    session = make_session()
    items = [session.add_to_reserve(text, today=D24) for text in "abc"]
    session.set_reserve_priority(items[1].id, priority=True)
    assert session.reserve == items
    assert [item.priority for item in session.reserve] == [False, True, False]
    session.set_reserve_priority(items[1].id, priority=False)
    assert not items[1].priority


def test_marking_is_allowed_on_a_frozen_list_and_a_struck_task() -> None:
    session = make_session()
    task = session.add("done already")
    session.strike(task.id, now=NOW)
    item = session.add_to_reserve("later", today=D24)
    session.lock()
    session.set_priority(task.id, priority=True)
    session.set_reserve_priority(item.id, priority=True)
    assert task.priority and item.priority


def test_marking_an_unknown_id_is_a_key_error() -> None:
    session = make_session()
    with pytest.raises(KeyError):
        session.set_priority("no-such-id", priority=True)
    with pytest.raises(KeyError):
        session.set_reserve_priority("no-such-id", priority=True)


# It follows the task everywhere.


def test_a_draw_carries_the_priority_both_ways() -> None:
    session = make_session()
    item = session.add_to_reserve("fix the bike", today=D24)
    session.set_reserve_priority(item.id, priority=True)
    task = session.draw_from_reserve(item.id)
    assert task.priority
    back = session.send_to_reserve(task.id, today=D24)
    assert (back.id, back.priority) == (item.id, True)


def test_a_draw_carries_a_cleared_priority_back() -> None:
    session = make_session()
    item = session.add_to_reserve("fix the bike", today=D24)
    session.set_reserve_priority(item.id, priority=True)
    task = session.draw_from_reserve(item.id)
    session.set_priority(task.id, priority=False)
    assert not session.send_to_reserve(task.id, today=D24).priority


def test_a_day_task_sent_back_makes_a_marked_item() -> None:
    session = make_session()
    task = session.add("call the bank")
    session.set_priority(task.id, priority=True)
    assert session.send_to_reserve(task.id, today=D24).priority


def test_the_rollover_returns_a_drawn_task_with_its_priority() -> None:
    session = make_session()
    item = session.add_to_reserve("fix the bike", today=D24)
    task = session.draw_from_reserve(item.id)
    session.set_priority(task.id, priority=True)
    session.roll_over(NEXT_DAY)
    (back,) = session.reserve
    assert (back.id, back.priority) == (item.id, True)


def test_the_rollover_sends_a_marked_day_task_as_a_marked_item() -> None:
    session = make_session()
    marked = session.add("call the bank")
    session.add("buy bread")
    session.set_priority(marked.id, priority=True)
    session.roll_over(NEXT_DAY)
    assert [(i.text, i.priority) for i in session.reserve] == [
        ("call the bank", True),
        ("buy bread", False),
    ]


def test_a_marked_duplicate_marks_the_existing_item() -> None:
    session = make_session()
    existing = session.add_to_reserve("Call the bank", today=D24)
    task = session.add("  call the bank ")
    session.set_priority(task.id, priority=True)
    session.roll_over(NEXT_DAY)
    assert session.reserve == [existing]
    assert existing.priority


def test_an_unmarked_duplicate_never_clears_a_priority() -> None:
    session = make_session()
    existing = session.add_to_reserve("call the bank", today=D24)
    session.set_reserve_priority(existing.id, priority=True)
    session.add("call the bank")
    session.roll_over(NEXT_DAY)
    assert session.reserve == [existing]
    assert existing.priority


def test_a_marked_duplicate_marks_an_item_added_by_the_same_rollover() -> None:
    session = make_session()
    session.add("call the bank")
    second = session.add("call the bank")
    session.set_priority(second.id, priority=True)
    session.roll_over(NEXT_DAY)
    (item,) = session.reserve
    assert (item.text, item.priority) == ("call the bank", True)


def test_a_marked_duplicate_marks_an_item_back_from_the_day() -> None:
    session = make_session()
    item = session.add_to_reserve("call the bank", today=D24)
    session.draw_from_reserve(item.id)
    duplicate = session.add("call the bank")
    session.set_priority(duplicate.id, priority=True)
    session.roll_over(NEXT_DAY)
    (back,) = session.reserve
    assert (back.id, back.priority) == (item.id, True)


def test_a_marked_recurring_task_is_dropped_with_its_priority() -> None:
    session = make_session()
    session.add_recurring("water plants", [0])
    (task,) = session.inject_recurring(D24)
    session.set_priority(task.id, priority=True)
    session.roll_over(NEXT_DAY)
    assert session.reserve == []


def test_undo_restores_the_priority() -> None:
    session = make_session()
    task = session.add("call the bank")
    session.set_priority(task.id, priority=True)
    session.delete(task.id, now=NOW)
    assert session.day.deletions[0].priority
    assert session.undo_last_deletion().priority


# App saves each change.


def test_app_saves_a_task_priority(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=lambda: NOW)
    task = app.add("call the bank")
    app.set_priority(task.id, priority=True)
    reopened = App.open(tmp_path, clock=lambda: NOW)
    assert reopened.session.day.tasks[0].priority


def test_app_saves_a_reserve_priority(tmp_path: Path) -> None:
    app = App.open(tmp_path, clock=lambda: NOW)
    item = app.add_to_reserve("fix the bike")
    app.set_reserve_priority(item.id, priority=True)
    reopened = App.open(tmp_path, clock=lambda: NOW)
    assert reopened.session.reserve[0].priority
