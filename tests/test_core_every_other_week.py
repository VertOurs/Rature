# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Every-other-week recurring templates: SPECIFICATION.md §2.5 and §2.7.7."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core.app import App, Cadence
from rature.core.models import Origin, RecurringItem
from rature.core.recurrence import cadence_on, due_on, monday_of, start_monday
from rature.core.session import Day, Session

PARIS = timezone(timedelta(hours=1))

# ISO weeks 52 and 53 of 2026, then 1 and 2 of 2027: 2026 has 53 weeks.
W52 = date(2026, 12, 21)
W53 = date(2026, 12, 28)
W01 = date(2027, 1, 4)
W02 = date(2027, 1, 11)


def biweekly(start: date, weekdays: list[int] | None = None) -> RecurringItem:
    return RecurringItem(
        text="swimming", weekdays=weekdays or [1], every_other_week_from=start
    )


def test_the_four_weeks_cross_a_53_week_year() -> None:
    # Pins the trap the rule avoids: two consecutive odd ISO weeks.
    weeks = [monday.isocalendar().week for monday in (W52, W53, W01, W02)]
    assert weeks == [52, 53, 1, 2]
    assert weeks[1] % 2 == weeks[2] % 2 == 1


def test_parity_alternates_across_the_year_boundary() -> None:
    item = biweekly(W52)
    tuesdays = [monday + timedelta(days=1) for monday in (W52, W53, W01, W02)]
    assert [bool(due_on(day, [item])) for day in tuesdays] == [
        True,
        False,
        True,
        False,
    ]


def test_parity_holds_before_the_stored_monday() -> None:
    item = biweekly(W01)
    assert due_on(W52 + timedelta(days=1), [item]) == [item]
    assert due_on(W53 + timedelta(days=1), [item]) == []


def test_an_active_week_still_needs_the_right_weekday() -> None:
    assert due_on(W52 + timedelta(days=2), [biweekly(W52)]) == []


def test_a_weekly_template_is_due_every_week() -> None:
    weekly = RecurringItem(text="water plants", weekdays=[1])
    tuesdays = [monday + timedelta(days=1) for monday in (W52, W53, W01, W02)]
    assert all(due_on(day, [weekly]) == [weekly] for day in tuesdays)


def test_monday_of_a_sunday_is_six_days_back() -> None:
    assert monday_of(date(2027, 1, 3)) == W53
    assert monday_of(W53) == W53


def test_cadence_on_reads_each_state() -> None:
    weekly = RecurringItem(text="water plants", weekdays=[1])
    assert cadence_on(weekly, W53) is Cadence.WEEKLY
    item = biweekly(W52)
    assert cadence_on(item, W52 + timedelta(days=6)) is (
        Cadence.EVERY_OTHER_FROM_THIS_WEEK
    )
    assert cadence_on(item, W53) is Cadence.EVERY_OTHER_FROM_NEXT_WEEK


def test_start_monday_for_each_cadence() -> None:
    sunday = date(2027, 1, 3)
    assert start_monday(Cadence.WEEKLY, sunday) is None
    assert start_monday(Cadence.WEEKLY, None) is None
    assert start_monday(Cadence.EVERY_OTHER_FROM_THIS_WEEK, sunday) == W53
    assert start_monday(Cadence.EVERY_OTHER_FROM_NEXT_WEEK, sunday) == W01


def test_start_monday_needs_today_for_every_other_week() -> None:
    with pytest.raises(ValueError):
        start_monday(Cadence.EVERY_OTHER_FROM_THIS_WEEK, None)


def test_start_monday_keeps_a_stored_monday_with_the_same_weeks() -> None:
    assert start_monday(Cadence.EVERY_OTHER_FROM_THIS_WEEK, W01, W52) == W52
    assert start_monday(Cadence.EVERY_OTHER_FROM_NEXT_WEEK, W53, W52) == W52


def test_start_monday_replaces_a_stored_monday_with_the_other_weeks() -> None:
    assert start_monday(Cadence.EVERY_OTHER_FROM_THIS_WEEK, W53, W52) == W53


def make_session() -> Session:
    return Session(Day(date=W52))


def test_add_recurring_every_other_week() -> None:
    session = make_session()
    item = session.add_recurring(
        "swimming", [1], cadence=Cadence.EVERY_OTHER_FROM_NEXT_WEEK, today=W52
    )
    assert item.every_other_week_from == W53


def test_add_recurring_every_other_week_without_today_is_refused() -> None:
    session = make_session()
    with pytest.raises(ValueError):
        session.add_recurring(
            "swimming", [1], cadence=Cadence.EVERY_OTHER_FROM_THIS_WEEK
        )
    assert session.recurring == []


def test_edit_recurring_keeps_the_weeks_when_not_given() -> None:
    session = make_session()
    item = session.add_recurring(
        "swimming", [1], cadence=Cadence.EVERY_OTHER_FROM_THIS_WEEK, today=W52
    )
    edited = session.edit_recurring(item.id, text="pool", weekdays=[3])
    assert edited.every_other_week_from == W52


def test_edit_recurring_back_to_weekly_clears_the_start() -> None:
    session = make_session()
    item = session.add_recurring(
        "swimming", [1], cadence=Cadence.EVERY_OTHER_FROM_THIS_WEEK, today=W52
    )
    edited = session.edit_recurring(item.id, cadence=Cadence.WEEKLY, today=W53)
    assert edited.every_other_week_from is None


def test_edit_recurring_weekly_to_every_other_week() -> None:
    session = make_session()
    item = session.add_recurring("swimming", [1])
    edited = session.edit_recurring(
        item.id, cadence=Cadence.EVERY_OTHER_FROM_NEXT_WEEK, today=W53
    )
    assert edited.every_other_week_from == W01


def test_inject_recurring_skips_an_inactive_week() -> None:
    session = make_session()
    session.add_recurring(
        "swimming", [1], cadence=Cadence.EVERY_OTHER_FROM_NEXT_WEEK, today=W52
    )
    assert session.inject_recurring(W52 + timedelta(days=1)) == []
    (task,) = session.inject_recurring(W53 + timedelta(days=1))
    assert (task.text, task.origin) == ("swimming", Origin.RECURRING)


class MovingClock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


def test_app_computes_the_monday_from_the_reference_date(data_dir: Path) -> None:
    # Monday 4 January 2027 at 02:00 still belongs to Sunday 3 January
    # (04:00 boundary), so "this week" is the week of 28 December.
    clock = MovingClock(datetime(2027, 1, 4, 2, 0, tzinfo=PARIS))
    app = App.open(data_dir, clock=clock)
    item = app.add_recurring("swimming", [1], Cadence.EVERY_OTHER_FROM_THIS_WEEK)
    assert item.every_other_week_from == W53
    assert app.cadence(item) is Cadence.EVERY_OTHER_FROM_THIS_WEEK
    clock.moment = datetime(2027, 1, 4, 5, 0, tzinfo=PARIS)
    assert app.cadence(item) is Cadence.EVERY_OTHER_FROM_NEXT_WEEK


def test_app_text_only_edit_does_not_shift_the_weeks(data_dir: Path) -> None:
    clock = MovingClock(datetime(2026, 12, 21, 9, 0, tzinfo=PARIS))
    app = App.open(data_dir, clock=clock)
    item = app.add_recurring("swimming", [1], Cadence.EVERY_OTHER_FROM_THIS_WEEK)
    clock.moment = datetime(2026, 12, 29, 9, 0, tzinfo=PARIS)
    edited = app.edit_recurring(item.id, text="pool")
    assert edited.every_other_week_from == W52
    assert app.cadence(edited) is Cadence.EVERY_OTHER_FROM_NEXT_WEEK


def test_app_resaving_the_preselected_cadence_keeps_the_monday(
    data_dir: Path,
) -> None:
    # What the form does on Save: it sends back the cadence core reported.
    clock = MovingClock(datetime(2026, 12, 21, 9, 0, tzinfo=PARIS))
    app = App.open(data_dir, clock=clock)
    item = app.add_recurring("swimming", [1], Cadence.EVERY_OTHER_FROM_THIS_WEEK)
    clock.moment = datetime(2027, 1, 13, 9, 0, tzinfo=PARIS)
    edited = app.edit_recurring(item.id, text="pool", cadence=app.cadence(item))
    assert edited.every_other_week_from == W52


def test_app_edit_back_to_weekly_is_saved(data_dir: Path) -> None:
    clock = MovingClock(datetime(2026, 12, 21, 9, 0, tzinfo=PARIS))
    app = App.open(data_dir, clock=clock)
    item = app.add_recurring("swimming", [1], Cadence.EVERY_OTHER_FROM_NEXT_WEEK)
    app.edit_recurring(item.id, cadence=Cadence.WEEKLY)
    reopened = App.open(data_dir, clock=clock)
    assert reopened.session.recurring[0].every_other_week_from is None


def test_week_a_and_week_b_alternate_over_four_weeks(data_dir: Path) -> None:
    """The real need: two activities in week A, two others in week B."""
    clock = MovingClock(datetime(2026, 12, 21, 9, 0, tzinfo=PARIS))
    app = App.open(data_dir, clock=clock)
    week_a = Cadence.EVERY_OTHER_FROM_THIS_WEEK
    week_b = Cadence.EVERY_OTHER_FROM_NEXT_WEEK
    app.add_recurring("swimming", [1], week_a)
    app.add_recurring("choir", [3], week_a)
    app.add_recurring("pottery", [1], week_b)
    app.add_recurring("climbing", [3], week_b)

    injected: dict[date, set[str]] = {}
    for offset in range(1, 28):
        day = W52 + timedelta(days=offset)
        clock.moment = datetime.combine(day, datetime.min.time(), PARIS).replace(hour=9)
        app.ensure_day()
        texts = {
            task.text
            for task in app.session.day.tasks
            if task.origin == Origin.RECURRING
        }
        injected.setdefault(monday_of(day), set()).update(texts)

    assert injected == {
        W52: {"swimming", "choir"},
        W53: {"pottery", "climbing"},
        W01: {"swimming", "choir"},
        W02: {"pottery", "climbing"},
    }
