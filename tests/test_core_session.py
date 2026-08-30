# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The day session operations and the rules they enforce."""

from datetime import date, datetime, timedelta, timezone

import pytest

from rature.core.models import Origin
from rature.core.session import Day, LockedError, Session

PARIS = timezone(timedelta(hours=2))
STAMP = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)


def make_session() -> Session:
    return Session(Day(date=date(2026, 8, 24)))


def test_add_assigns_sequential_numbers() -> None:
    session = make_session()
    nums = [session.add("a").num, session.add("b").num, session.add("c").num]
    assert nums == [1, 2, 3]
    assert session.day.counter == 4


def test_add_stores_text_verbatim() -> None:
    session = make_session()
    assert session.add("  MTG w/ P  ").text == "  MTG w/ P  "


def test_add_on_a_frozen_list_is_refused() -> None:
    session = make_session()
    session.lock()
    with pytest.raises(LockedError):
        session.add("nope")


def test_a_deleted_number_is_never_reused() -> None:
    session = make_session()
    first = session.add("first")
    session.add("second")
    session.delete(first.id)
    assert session.add("third").num == 3


def test_strike_sets_done_and_a_timestamp() -> None:
    session = make_session()
    task = session.add("thing")
    session.strike(task.id, now=STAMP)
    assert task.done is True
    assert task.done_at == STAMP


def test_strike_default_timestamp_is_timezone_aware() -> None:
    session = make_session()
    task = session.add("thing")
    session.strike(task.id)
    assert task.done_at is not None
    assert task.done_at.tzinfo is not None


def test_strike_rejects_a_naive_now() -> None:
    session = make_session()
    task = session.add("thing")
    with pytest.raises(ValueError):
        session.strike(task.id, now=datetime(2026, 8, 24, 14, 32, 7))


def test_strike_twice_is_refused() -> None:
    session = make_session()
    task = session.add("thing")
    session.strike(task.id, now=STAMP)
    with pytest.raises(ValueError):
        session.strike(task.id, now=STAMP)


def test_unstrike_clears_done_and_the_timestamp() -> None:
    session = make_session()
    task = session.add("thing")
    session.strike(task.id, now=STAMP)
    session.unstrike(task.id)
    assert task.done is False
    assert task.done_at is None


def test_unstrike_when_not_struck_is_refused() -> None:
    session = make_session()
    task = session.add("thing")
    with pytest.raises(ValueError):
        session.unstrike(task.id)


def test_strike_rename_delete_reorder_work_while_frozen() -> None:
    session = make_session()
    one = session.add("one")
    two = session.add("two")
    session.lock()
    session.strike(one.id, now=STAMP)
    session.rename(two.id, "two bis")
    session.reorder([two.id, one.id])
    session.delete(one.id)
    assert [task.text for task in session.day.tasks] == ["two bis"]


def test_rename_changes_the_text_and_keeps_the_number() -> None:
    session = make_session()
    task = session.add("draft")
    session.rename(task.id, "final")
    assert (task.text, task.num) == ("final", 1)


def test_delete_moves_a_full_entry_to_the_journal() -> None:
    session = make_session()
    session.add("keep")
    gone = session.add("drop")
    session.delete(gone.id, now=STAMP)
    assert gone not in session.day.tasks
    (entry,) = session.day.deletions
    assert (entry.id, entry.num, entry.text, entry.origin, entry.deleted_at) == (
        gone.id,
        2,
        "drop",
        Origin.DAY,
        STAMP,
    )


def test_a_struck_task_can_be_deleted() -> None:
    session = make_session()
    task = session.add("thing")
    session.strike(task.id, now=STAMP)
    session.delete(task.id, now=STAMP)
    assert session.day.tasks == []
    assert len(session.day.deletions) == 1


def test_reorder_applies_a_permutation() -> None:
    session = make_session()
    one, two, three = session.add("1"), session.add("2"), session.add("3")
    session.reorder([three.id, one.id, two.id])
    assert [task.num for task in session.day.tasks] == [3, 1, 2]


def test_reorder_rejects_a_non_permutation() -> None:
    session = make_session()
    one = session.add("1")
    session.add("2")
    with pytest.raises(ValueError):
        session.reorder([one.id])


def test_view_is_the_struck_block_then_the_active_tasks() -> None:
    session = make_session()
    one, two, three, four = (session.add(str(n)) for n in range(1, 5))
    session.strike(two.id, now=STAMP)
    session.strike(four.id, now=STAMP)
    assert session.struck == [two, four]
    assert session.active == [one, three]
    assert session.view() == [two, four, one, three]


def test_lock_and_unlock_toggle_the_flag() -> None:
    session = make_session()
    session.lock()
    assert session.day.locked is True
    session.unlock()
    assert session.day.locked is False


def test_an_unknown_task_id_is_a_key_error() -> None:
    session = make_session()
    with pytest.raises(KeyError):
        session.strike("no-such-id")


def test_day_round_trips() -> None:
    session = make_session()
    session.add("active")
    struck = session.add("struck")
    session.strike(struck.id, now=STAMP)
    dropped = session.add("dropped")
    session.delete(dropped.id, now=STAMP)
    assert Day.from_dict(session.day.to_dict()) == session.day
