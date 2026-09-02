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


def test_add_struck_creates_a_struck_task() -> None:
    session = make_session()
    task = session.add_struck("  called back  ", now=STAMP)
    assert (task.done, task.done_at, task.text) == (True, STAMP, "  called back  ")
    assert session.struck == [task]
    assert session.active == []


def test_add_struck_takes_the_next_number_and_advances_the_counter() -> None:
    session = make_session()
    first = session.add("live")
    struck = session.add_struck("done", now=STAMP)
    assert (first.num, struck.num) == (1, 2)
    assert session.day.counter == 3


def test_add_struck_lands_in_the_struck_block() -> None:
    session = make_session()
    live = session.add("live")
    struck = session.add_struck("done", now=STAMP)
    assert session.view() == [struck, live]


def test_add_struck_on_a_frozen_list_is_refused() -> None:
    session = make_session()
    session.lock()
    with pytest.raises(LockedError):
        session.add_struck("nope", now=STAMP)


def test_add_struck_requires_an_aware_timestamp() -> None:
    session = make_session()
    with pytest.raises(ValueError):
        session.add_struck("done", now=datetime(2026, 8, 24, 14, 0, 0))


def test_a_deleted_number_is_never_reused() -> None:
    session = make_session()
    first = session.add("first")
    session.add("second")
    session.delete(first.id, now=STAMP)
    assert session.add("third").num == 3


def test_strike_sets_done_and_a_timestamp() -> None:
    session = make_session()
    task = session.add("thing")
    session.strike(task.id, now=STAMP)
    assert task.done is True
    assert task.done_at == STAMP


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
    session.delete(one.id, now=STAMP)
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
    assert (
        entry.id,
        entry.num,
        entry.text,
        entry.origin,
        entry.deleted_at,
        entry.index,
    ) == (
        gone.id,
        2,
        "drop",
        Origin.DAY,
        STAMP,
        1,
    )


def test_a_struck_task_can_be_deleted() -> None:
    session = make_session()
    task = session.add("thing")
    session.strike(task.id, now=STAMP)
    session.delete(task.id, now=STAMP)
    assert session.day.tasks == []
    assert len(session.day.deletions) == 1


def test_undo_restores_the_last_deleted_task_and_drops_the_entry() -> None:
    session = make_session()
    session.add("keep")
    gone = session.add("drop")
    session.delete(gone.id, now=STAMP)

    restored = session.undo_last_deletion()

    assert (restored.id, restored.num, restored.text) == (gone.id, 2, "drop")
    assert session.day.deletions == []
    assert [task.text for task in session.day.tasks] == ["keep", "drop"]


def test_undo_puts_the_task_back_at_its_recorded_index() -> None:
    session = make_session()
    a, b, c = session.add("a"), session.add("b"), session.add("c")
    session.delete(b.id, now=STAMP)
    session.undo_last_deletion()
    assert [task.id for task in session.day.tasks] == [a.id, b.id, c.id]


def test_undo_clamps_the_index_when_the_list_has_shrunk() -> None:
    session = make_session()
    a, b, c = session.add("a"), session.add("b"), session.add("c")
    session.delete(c.id, now=STAMP)  # index 2
    session.delete(a.id, now=STAMP)  # list is now [b]
    session.undo_last_deletion()  # a restored at min(0, 1)
    session.undo_last_deletion()  # c restored at min(2, 2)
    assert [task.id for task in session.day.tasks] == [a.id, b.id, c.id]


def test_undo_restores_a_struck_task_struck() -> None:
    session = make_session()
    task = session.add("done thing")
    session.strike(task.id, now=STAMP)
    session.delete(task.id, now=STAMP)
    restored = session.undo_last_deletion()
    assert restored.done is True
    assert restored.done_at == STAMP


def test_undo_takes_only_the_most_recent_deletion() -> None:
    session = make_session()
    first = session.add("first")
    second = session.add("second")
    session.delete(first.id, now=STAMP)
    session.delete(second.id, now=STAMP)

    assert session.undo_last_deletion().id == second.id
    assert session.undo_last_deletion().id == first.id
    assert session.day.deletions == []


def test_undo_with_an_empty_journal_is_refused() -> None:
    session = make_session()
    with pytest.raises(ValueError):
        session.undo_last_deletion()


def test_undo_does_not_reuse_the_freed_number() -> None:
    session = make_session()
    session.add("one")
    two = session.add("two")
    session.add("three")
    session.delete(two.id, now=STAMP)
    session.undo_last_deletion()
    assert session.add("four").num == 4
    assert session._task(two.id).num == 2


def test_undo_works_while_the_list_is_frozen() -> None:
    session = make_session()
    task = session.add("thing")
    session.delete(task.id, now=STAMP)
    session.lock()
    session.undo_last_deletion()
    assert [t.id for t in session.day.tasks] == [task.id]


def test_undo_restores_a_reserve_task_with_its_source() -> None:
    session = make_session()
    item = session.add_to_reserve("from reserve", today=date(2026, 8, 20))
    drawn = session.draw_from_reserve(item.id)
    session.delete(drawn.id, now=STAMP)

    restored = session.undo_last_deletion()

    assert restored.origin == Origin.RESERVE
    assert restored.source_id == item.id
    assert restored.source_created == date(2026, 8, 20)


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


def test_move_before_places_the_task_ahead_of_the_target() -> None:
    session = make_session()
    session.add("1")
    two, three = session.add("2"), session.add("3")
    session.move_before(three.id, two.id)
    assert [task.num for task in session.day.tasks] == [1, 3, 2]


def test_move_before_none_moves_the_task_to_the_end() -> None:
    session = make_session()
    one = session.add("1")
    session.add("2")
    session.add("3")
    session.move_before(one.id, None)
    assert [task.num for task in session.day.tasks] == [2, 3, 1]


def test_move_before_rejects_an_unknown_task_id() -> None:
    session = make_session()
    target = session.add("1")
    with pytest.raises(KeyError):
        session.move_before("no-such-id", target.id)


def test_move_before_rejects_an_unknown_target_id() -> None:
    session = make_session()
    task = session.add("1")
    with pytest.raises(KeyError):
        session.move_before(task.id, "no-such-id")


def test_move_before_itself_is_a_no_op() -> None:
    session = make_session()
    one = session.add("1")
    session.add("2")
    session.move_before(one.id, one.id)
    assert [task.num for task in session.day.tasks] == [1, 2]


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
        session.strike("no-such-id", now=STAMP)


def test_day_round_trips() -> None:
    session = make_session()
    session.add("active")
    struck = session.add("struck")
    session.strike(struck.id, now=STAMP)
    dropped = session.add("dropped")
    session.delete(dropped.id, now=STAMP)
    assert Day.from_dict(session.day.to_dict()) == session.day
