# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Recurring template CRUD, which templates apply, and their injection."""

from datetime import date

import pytest

from rature.core.models import Origin, RecurringItem
from rature.core.recurrence import due_on
from rature.core.session import Day, LockedError, Session

TODAY = date(2026, 8, 24)


def make_session() -> Session:
    return Session(Day(date=TODAY))


def test_due_on_returns_the_matching_templates_in_order() -> None:
    mon_wed = RecurringItem(text="mon/wed", weekdays=[0, 2])
    every = RecurringItem(text="every", weekdays=[0, 1, 2, 3, 4, 5, 6])
    tue = RecurringItem(text="tue", weekdays=[1])
    assert due_on(2, [mon_wed, every, tue]) == [mon_wed, every]


def test_due_on_an_empty_list_is_empty() -> None:
    assert due_on(0, []) == []


def test_due_on_rejects_a_weekday_out_of_range() -> None:
    with pytest.raises(ValueError):
        due_on(7, [])


def test_add_recurring_appends_and_validates() -> None:
    session = make_session()
    item = session.add_recurring("water plants", [0, 3])
    assert session.recurring == [item]
    with pytest.raises(ValueError):
        session.add_recurring("broken", [])
    with pytest.raises(ValueError):
        session.add_recurring("broken", [7])


def test_add_recurring_is_allowed_while_the_day_is_frozen() -> None:
    session = make_session()
    session.lock()
    assert session.add_recurring("ok", [1]).weekdays == [1]


def test_edit_recurring_changes_text_only() -> None:
    session = make_session()
    item = session.add_recurring("draft", [0, 3])
    edited = session.edit_recurring(item.id, text="final")
    assert (edited.id, edited.text, edited.weekdays) == (item.id, "final", [0, 3])
    assert session.recurring == [edited]


def test_edit_recurring_changes_weekdays_only() -> None:
    session = make_session()
    item = session.add_recurring("thing", [0])
    edited = session.edit_recurring(item.id, weekdays=[5, 6])
    assert (edited.id, edited.text, edited.weekdays) == (item.id, "thing", [5, 6])


def test_edit_recurring_rejects_invalid_weekdays_and_keeps_the_old() -> None:
    session = make_session()
    item = session.add_recurring("thing", [0, 3])
    with pytest.raises(ValueError):
        session.edit_recurring(item.id, weekdays=[])
    assert session.recurring == [item]


def test_delete_recurring_removes_it() -> None:
    session = make_session()
    item = session.add_recurring("thing", [0])
    session.delete_recurring(item.id)
    assert session.recurring == []


def test_recurring_lookup_skips_past_a_non_matching_item() -> None:
    session = make_session()
    session.add_recurring("first", [0])
    second = session.add_recurring("second", [1])
    edited = session.edit_recurring(second.id, text="second, renamed")
    assert edited.text == "second, renamed"


def test_an_unknown_recurring_id_is_a_key_error() -> None:
    session = make_session()
    with pytest.raises(KeyError):
        session.edit_recurring("no-such-id", text="x")


def test_inject_recurring_creates_recurring_origin_tasks() -> None:
    session = make_session()
    session.add("a day task")
    mon = session.add_recurring("monday only", [0])
    tue = session.add_recurring("tuesday only", [1])
    created = session.inject_recurring(0)
    assert [task.text for task in created] == ["monday only"]
    task = created[0]
    assert (task.origin, task.template_id, task.num) == (Origin.RECURRING, mon.id, 2)
    assert session.day.counter == 3
    assert tue.id not in {t.template_id for t in session.day.tasks}


def test_inject_recurring_is_refused_while_the_day_is_frozen() -> None:
    session = make_session()
    session.add_recurring("daily", [0, 1, 2, 3, 4, 5, 6])
    session.lock()
    with pytest.raises(LockedError):
        session.inject_recurring(0)
