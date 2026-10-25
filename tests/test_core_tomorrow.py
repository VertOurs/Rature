# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Tomorrow list, SPECIFICATION.md §2.5 and §2.7.9."""

from datetime import date

import pytest

from rature.core.models import Origin
from rature.core.session import Day, Session

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
    assert first.source_id is None
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
    session.set_tomorrow_priority(second.id, True)
    assert second.priority
    assert session.tomorrow == [first, second]
    session.set_tomorrow_priority(second.id, False)
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
        lambda s, i: s.set_tomorrow_priority(i, True),
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
    session.set_tomorrow_priority(a.id, True)
    session.move_tomorrow_before(b.id, a.id)
    session.delete_from_tomorrow(a.id)
    assert session.tomorrow == [b]
