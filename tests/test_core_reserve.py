# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Reserve operations and the draw from reserve."""

from datetime import date, datetime, timedelta, timezone

import pytest

from rature.core.models import Origin
from rature.core.session import Day, LockedError, Session

PARIS = timezone(timedelta(hours=2))
STAMP = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)
TODAY = date(2026, 8, 24)


def make_session() -> Session:
    return Session(Day(date=TODAY))


def test_a_bare_session_has_an_empty_reserve_and_recurring() -> None:
    session = Session(Day(date=TODAY))
    assert session.reserve == []
    assert session.recurring == []


def test_add_to_reserve_appends_with_the_given_date() -> None:
    session = make_session()
    item = session.add_to_reserve("someday", today=date(2026, 8, 20))
    assert session.reserve == [item]
    assert item.created == date(2026, 8, 20)


def test_add_to_reserve_never_de_duplicates() -> None:
    session = make_session()
    session.add_to_reserve("same", today=TODAY)
    session.add_to_reserve("same", today=TODAY)
    assert [item.text for item in session.reserve] == ["same", "same"]
    assert session.reserve[0].id != session.reserve[1].id


def test_reserve_edits_work_while_the_day_is_frozen() -> None:
    session = make_session()
    item = session.add_to_reserve("draft", today=TODAY)
    session.lock()
    session.rename_reserve(item.id, "final")
    assert session._reserve_item(item.id).text == "final"
    session.delete_from_reserve(item.id)
    assert session.reserve == []


def test_reserve_lookup_skips_past_a_non_matching_item() -> None:
    session = make_session()
    session.add_to_reserve("first", today=TODAY)
    second = session.add_to_reserve("second", today=TODAY)
    session.rename_reserve(second.id, "second, renamed")
    assert session._reserve_item(second.id).text == "second, renamed"


def test_an_unknown_reserve_id_is_a_key_error() -> None:
    session = make_session()
    with pytest.raises(KeyError):
        session.rename_reserve("no-such-id", "x")


def test_draw_moves_the_item_into_the_day() -> None:
    session = make_session()
    item = session.add_to_reserve("do this", today=TODAY)
    task = session.draw_from_reserve(item.id)
    assert session.reserve == []
    assert session.day.tasks == [task]
    assert task.text == "do this"
    assert task.origin == Origin.RESERVE
    assert task.source_id == item.id
    assert task.source_created == item.created


def test_draw_assigns_the_next_number() -> None:
    session = make_session()
    session.add("first day task")
    item = session.add_to_reserve("from reserve", today=TODAY)
    assert session.draw_from_reserve(item.id).num == 2
    assert session.day.counter == 3


def test_draw_is_refused_while_the_day_is_frozen() -> None:
    session = make_session()
    item = session.add_to_reserve("later", today=TODAY)
    session.lock()
    with pytest.raises(LockedError):
        session.draw_from_reserve(item.id)
    assert session.reserve == [item]


def test_a_drawn_then_deleted_task_journals_its_source() -> None:
    session = make_session()
    item = session.add_to_reserve("regret", today=TODAY)
    task = session.draw_from_reserve(item.id)
    session.delete(task.id, now=STAMP)
    assert session.day.deletions[0].source_id == item.id
