# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Tomorrow list, SPECIFICATION.md §2.5 and §2.7.9."""

from datetime import date, datetime, timedelta, timezone

import pytest

from rature.core.models import Origin
from rature.core.recurrence import Cadence
from rature.core.session import Day, LockedError, Session

PARIS = timezone(timedelta(hours=2))
STAMP = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)
TODAY = date(2026, 8, 24)


def make_session() -> Session:
    return Session(Day(date=TODAY))


def frozen_session() -> Session:
    session = make_session()
    session.lock()
    return session


def test_a_bare_session_has_nothing_prepared() -> None:
    assert make_session().tomorrow == []


def test_add_to_tomorrow_appends_a_day_origin_task() -> None:
    session = make_session()
    first = session.add_to_tomorrow("book the train")
    second = session.add_to_tomorrow("call the insurance")
    assert session.tomorrow == [first, second]
    assert first.origin == Origin.DAY
    assert first.source is None
    assert not first.priority


def test_add_to_tomorrow_never_de_duplicates() -> None:
    session = make_session()
    session.add_to_tomorrow("same")
    session.add_to_tomorrow("same")
    assert [task.text for task in session.tomorrow] == ["same", "same"]
    assert session.tomorrow[0].id != session.tomorrow[1].id


def test_add_to_tomorrow_touches_neither_the_day_nor_its_counter() -> None:
    session = make_session()
    session.add_to_tomorrow("prepared")
    assert session.day.tasks == []
    assert session.day.counter == 1


def test_rename_tomorrow_replaces_the_text() -> None:
    session = make_session()
    task = session.add_to_tomorrow("draft")
    session.rename_tomorrow(task.id, "final")
    assert session.tomorrow[0].text == "final"


def test_set_tomorrow_priority_marks_and_unmarks_without_moving() -> None:
    session = make_session()
    first = session.add_to_tomorrow("first")
    second = session.add_to_tomorrow("second")
    session.set_tomorrow_priority(second.id, priority=True)
    assert second.priority
    assert session.tomorrow == [first, second]
    session.set_tomorrow_priority(second.id, priority=False)
    assert not second.priority


def test_delete_from_tomorrow_leaves_no_journal_entry() -> None:
    session = make_session()
    task = session.add_to_tomorrow("never mind")
    session.delete_from_tomorrow(task.id)
    assert session.tomorrow == []
    assert session.day.deletions == []


def test_move_tomorrow_before_reorders_with_move_before_rule() -> None:
    session = make_session()
    a, b, c = (session.add_to_tomorrow(text) for text in "abc")
    session.move_tomorrow_before(c.id, a.id)
    assert session.tomorrow == [c, a, b]
    session.move_tomorrow_before(c.id, None)
    assert session.tomorrow == [a, b, c]


@pytest.mark.parametrize(
    "operation",
    [
        lambda s, i: s.rename_tomorrow(i, "x"),
        lambda s, i: s.set_tomorrow_priority(i, priority=True),
        lambda s, i: s.delete_from_tomorrow(i),
        lambda s, i: s.move_tomorrow_before(i, None),
    ],
)
def test_an_unknown_prepared_task_raises_key_error(operation) -> None:
    with pytest.raises(KeyError):
        operation(make_session(), "nope")


def test_editing_tomorrow_is_allowed_on_a_frozen_day() -> None:
    session = frozen_session()
    a = session.add_to_tomorrow("a")
    b = session.add_to_tomorrow("b")
    session.rename_tomorrow(a.id, "a, renamed")
    session.set_tomorrow_priority(a.id, priority=True)
    session.move_tomorrow_before(b.id, a.id)
    session.delete_from_tomorrow(a.id)
    assert session.tomorrow == [b]


# Move to tomorrow, from the day.


def test_move_to_tomorrow_keeps_the_task_but_not_its_number() -> None:
    session = make_session()
    session.add("stays")
    task = session.add("later")
    session.set_priority(task.id, priority=True)
    prepared = session.move_to_tomorrow(task.id)
    assert session.tomorrow == [prepared]
    assert (prepared.id, prepared.text, prepared.origin) == (
        task.id,
        "later",
        Origin.DAY,
    )
    assert prepared.priority
    assert "num" not in prepared.to_dict()
    assert [t.text for t in session.day.tasks] == ["stays"]


def test_move_to_tomorrow_leaves_no_trace_and_never_reuses_the_number() -> None:
    session = make_session()
    task = session.add("later")
    session.move_to_tomorrow(task.id)
    assert session.day.deletions == []
    assert session.day.counter == 2
    assert session.add("next").num == 2


def test_move_to_tomorrow_keeps_the_reserve_link() -> None:
    session = make_session()
    item = session.add_to_reserve("from the reserve", today=date(2026, 8, 20))
    task = session.draw_from_reserve(item.id)
    prepared = session.move_to_tomorrow(task.id)
    assert prepared.origin == Origin.RESERVE
    assert (prepared.source.id, prepared.source.created) == (
        item.id,
        date(2026, 8, 20),
    )


def test_move_to_tomorrow_goes_to_the_end() -> None:
    session = make_session()
    first = session.add_to_tomorrow("first")
    task = session.add("moved")
    assert session.tomorrow == [first, session.move_to_tomorrow(task.id)]


def test_move_to_tomorrow_refuses_a_struck_task() -> None:
    session = make_session()
    task = session.add("done")
    session.strike(task.id, now=STAMP)
    with pytest.raises(ValueError):
        session.move_to_tomorrow(task.id)
    assert session.tomorrow == []


def test_move_to_tomorrow_refuses_a_recurring_task() -> None:
    session = make_session()
    session.add_recurring("water plants", [0])
    (task,) = session.inject_recurring(TODAY)
    with pytest.raises(ValueError):
        session.move_to_tomorrow(task.id)
    assert session.tomorrow == []


def test_move_to_tomorrow_is_allowed_on_a_frozen_list() -> None:
    session = make_session()
    task = session.add("later")
    session.lock()
    session.move_to_tomorrow(task.id)
    assert session.day.tasks == []


# Move to tomorrow, from the reserve.


def test_move_reserve_to_tomorrow_is_a_move_with_a_link_back() -> None:
    session = make_session()
    item = session.add_to_reserve("someday", today=date(2026, 8, 20))
    session.set_reserve_priority(item.id, priority=True)
    prepared = session.move_reserve_to_tomorrow(item.id)
    assert session.reserve == []
    assert session.tomorrow == [prepared]
    assert prepared.origin == Origin.RESERVE
    assert (prepared.text, prepared.source.id, prepared.source.created) == (
        "someday",
        item.id,
        date(2026, 8, 20),
    )
    assert prepared.priority


def test_move_reserve_to_tomorrow_is_allowed_on_a_frozen_day() -> None:
    session = frozen_session()
    item = session.add_to_reserve("someday", today=TODAY)
    session.move_reserve_to_tomorrow(item.id)
    assert session.reserve == []


def test_move_reserve_to_tomorrow_unknown_item_raises_key_error() -> None:
    with pytest.raises(KeyError):
        make_session().move_reserve_to_tomorrow("nope")


# Move to today.


def test_move_to_today_gives_the_next_number_at_the_end() -> None:
    session = make_session()
    session.add("first")
    prepared = session.add_to_tomorrow("prepared")
    session.set_tomorrow_priority(prepared.id, priority=True)
    task = session.move_to_today(prepared.id)
    assert session.tomorrow == []
    assert session.day.tasks[-1] is task
    assert (task.id, task.num, task.text, task.origin) == (
        prepared.id,
        2,
        "prepared",
        Origin.DAY,
    )
    assert task.priority
    assert not task.done
    assert session.day.counter == 3


def test_move_to_today_keeps_the_reserve_link() -> None:
    session = make_session()
    item = session.add_to_reserve("someday", today=date(2026, 8, 20))
    prepared = session.move_reserve_to_tomorrow(item.id)
    task = session.move_to_today(prepared.id)
    assert task.origin == Origin.RESERVE
    assert (task.source.id, task.source.created) == (item.id, date(2026, 8, 20))


def test_a_task_moved_to_tomorrow_by_mistake_comes_back_with_a_new_number() -> None:
    session = make_session()
    task = session.add("oops")
    back = session.move_to_today(session.move_to_tomorrow(task.id).id)
    assert back.id == task.id
    assert back.num == 2


def test_move_to_today_is_refused_on_a_frozen_list() -> None:
    session = make_session()
    prepared = session.add_to_tomorrow("prepared")
    session.lock()
    with pytest.raises(LockedError):
        session.move_to_today(prepared.id)
    assert session.tomorrow == [prepared]
    assert session.day.tasks == []
    assert session.day.counter == 1


def test_move_to_today_unknown_task_raises_key_error() -> None:
    with pytest.raises(KeyError):
        make_session().move_to_today("nope")


# Send back to the reserve, from Tomorrow.


def test_send_tomorrow_to_reserve_returns_a_drawn_item_as_it_was() -> None:
    session = make_session()
    item = session.add_to_reserve("someday", today=date(2026, 8, 20))
    prepared = session.move_reserve_to_tomorrow(item.id)
    session.rename_tomorrow(prepared.id, "someday, renamed")
    session.set_tomorrow_priority(prepared.id, priority=True)
    back = session.send_tomorrow_to_reserve(prepared.id, today=TODAY)
    assert session.tomorrow == []
    assert session.reserve == [back]
    assert (back.id, back.text, back.created) == (
        item.id,
        "someday, renamed",
        date(2026, 8, 20),
    )
    assert back.priority


def test_send_tomorrow_to_reserve_makes_a_new_item_from_a_day_task() -> None:
    session = make_session()
    session.add_to_reserve("same", today=date(2026, 8, 20))
    prepared = session.add_to_tomorrow("same")
    back = session.send_tomorrow_to_reserve(prepared.id, today=TODAY)
    assert back.created == TODAY
    assert back.id != prepared.id
    assert [item.text for item in session.reserve] == ["same", "same"]


def test_send_tomorrow_to_reserve_is_allowed_on_a_frozen_day() -> None:
    session = frozen_session()
    prepared = session.add_to_tomorrow("prepared")
    session.send_tomorrow_to_reserve(prepared.id, today=TODAY)
    assert session.tomorrow == []


def test_send_tomorrow_to_reserve_unknown_task_raises_key_error() -> None:
    with pytest.raises(KeyError):
        make_session().send_tomorrow_to_reserve("nope", today=TODAY)


# Recurring tasks due tomorrow, shown read-only.

SUNDAY = date(2026, 8, 30)


def test_recurring_due_tomorrow_reads_the_next_weekday_in_list_order() -> None:
    session = make_session()
    later = session.add_recurring("weekly backup", [0])
    session.add_recurring("only on sunday", [6])
    first = session.add_recurring("water plants", [0, 3])
    assert session.recurring_due_tomorrow(SUNDAY) == [later, first]


def test_recurring_due_tomorrow_is_empty_without_a_match() -> None:
    session = make_session()
    session.add_recurring("only on sunday", [6])
    assert session.recurring_due_tomorrow(SUNDAY) == []


def test_recurring_due_tomorrow_follows_the_parity_across_a_week_change() -> None:
    session = make_session()
    # Active from the week of 2026-08-24: due Monday 24, not Monday 31.
    this_week = session.add_recurring(
        "swim", [0], cadence=Cadence.EVERY_OTHER_FROM_THIS_WEEK, today=TODAY
    )
    next_week = session.add_recurring(
        "run", [0], cadence=Cadence.EVERY_OTHER_FROM_NEXT_WEEK, today=TODAY
    )
    assert session.recurring_due_tomorrow(SUNDAY) == [next_week]
    assert session.recurring_due_tomorrow(date(2026, 8, 23)) == [this_week]


def test_recurring_due_tomorrow_changes_nothing() -> None:
    session = make_session()
    session.add_recurring("weekly backup", [0])
    session.recurring_due_tomorrow(SUNDAY)
    assert session.day.tasks == []
    assert session.tomorrow == []
    assert session.day.counter == 1
