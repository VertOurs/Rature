# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The day rollover: the 04:00 boundary, the six steps, multi-day, midnight, DST."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from rature.core.models import Origin, RecurringItem, ReserveItem
from rature.core.session import Day, Session, reference_date
from rature.core.storage import archive

PARIS = timezone(timedelta(hours=2))
# A real zone, unlike the fixed-offset PARIS above: its offset changes
# across the DST transitions the tests at the bottom cross.
PARIS_TZ = ZoneInfo("Europe/Paris")
STAMP = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)
D24 = date(2026, 8, 24)
D25 = date(2026, 8, 25)
NEXT_MORNING = datetime(2026, 8, 25, 9, 0)


def session_on(
    day_date: date = D24,
    *,
    reserve: list[ReserveItem] | None = None,
    recurring: list[RecurringItem] | None = None,
) -> Session:
    return Session(Day(date=day_date), reserve=reserve, recurring=recurring)


def test_reference_date_before_four_is_the_previous_day() -> None:
    assert reference_date(datetime(2026, 8, 25, 1, 0)) == D24


def test_reference_date_at_four_is_the_same_day() -> None:
    assert reference_date(datetime(2026, 8, 25, 4, 0, 0)) == D25


def test_reference_date_just_before_four_is_the_previous_day() -> None:
    assert reference_date(datetime(2026, 8, 25, 3, 59, 59)) == D24


def test_reference_date_in_the_evening_is_the_same_day() -> None:
    assert reference_date(datetime(2026, 8, 25, 23, 0)) == D25


def test_reference_date_follows_the_wall_clock_of_an_aware_now() -> None:
    assert reference_date(datetime(2026, 8, 25, 1, 0, tzinfo=PARIS)) == D24


def test_rollover_due_when_the_reference_date_moved_forward() -> None:
    assert session_on(D24).rollover_due(NEXT_MORNING) is True


def test_no_rollover_when_the_reference_date_is_unchanged() -> None:
    assert session_on(D24).rollover_due(datetime(2026, 8, 24, 23, 0)) is False


def test_no_rollover_when_the_clock_went_backward() -> None:
    assert session_on(D25).rollover_due(datetime(2026, 8, 24, 12, 0)) is False


def test_roll_over_when_not_due_raises() -> None:
    with pytest.raises(ValueError):
        session_on(D24).roll_over(datetime(2026, 8, 24, 23, 0))


def test_roll_over_returns_the_old_day_and_starts_a_fresh_one() -> None:
    session = session_on(D24)
    session.add("something")
    old = session.roll_over(NEXT_MORNING)
    assert old.date == D24
    assert session.day.date == D25
    assert session.day.locked is False
    assert session.day.counter == 1


def test_roll_over_moves_the_deletion_journal_with_the_old_day() -> None:
    session = session_on(D24)
    gone = session.add("gone")
    session.delete(gone.id, now=STAMP)
    old = session.roll_over(NEXT_MORNING)
    assert len(old.deletions) == 1
    assert session.day.deletions == []


def test_an_unfinished_reserve_task_returns_by_source_id() -> None:
    session = session_on(D24)
    origin = session.add_to_reserve("groceries", today=date(2026, 8, 18))
    session.draw_from_reserve(origin.id)
    session.roll_over(NEXT_MORNING)
    (back,) = session.reserve
    assert (back.id, back.text, back.created) == (
        origin.id,
        "groceries",
        date(2026, 8, 18),
    )


def test_a_renamed_reserve_task_returns_with_the_new_text() -> None:
    session = session_on(D24)
    origin = session.add_to_reserve("old name", today=date(2026, 8, 18))
    task = session.draw_from_reserve(origin.id)
    session.rename(task.id, "new name")
    session.roll_over(NEXT_MORNING)
    assert (session.reserve[0].id, session.reserve[0].text) == (origin.id, "new name")


def test_source_created_survives_reserve_day_reserve_day() -> None:
    session = session_on(D24)
    origin = session.add_to_reserve("errand", today=date(2026, 8, 10))
    session.draw_from_reserve(origin.id)
    session.roll_over(NEXT_MORNING)
    again = session.draw_from_reserve(session.reserve[0].id)
    assert again.source_created == date(2026, 8, 10)
    session.roll_over(datetime(2026, 8, 26, 9, 0))
    assert session.reserve[0].created == date(2026, 8, 10)


def test_step_2_does_not_dedup_against_a_matching_day_task() -> None:
    session = session_on(D24)
    origin = session.add_to_reserve("shared text", today=date(2026, 8, 1))
    session.draw_from_reserve(origin.id)
    session.add("shared text")
    session.roll_over(NEXT_MORNING)
    assert [item.id for item in session.reserve] == [origin.id]


def test_an_unfinished_day_task_goes_to_the_reserve_verbatim() -> None:
    session = session_on(D24)
    session.add("  buy milk  ")
    session.roll_over(NEXT_MORNING)
    assert [item.text for item in session.reserve] == ["  buy milk  "]
    assert session.reserve[0].created == D25


def test_day_tasks_are_deduped_on_trimmed_casefolded_text() -> None:
    session = session_on(D24)
    session.add("Café")
    session.add("  café ")
    session.roll_over(NEXT_MORNING)
    assert [item.text for item in session.reserve] == ["Café"]


def test_day_task_dedup_against_an_existing_reserve_entry() -> None:
    session = session_on(
        D24, reserve=[ReserveItem(text="buy milk", created=date(2026, 8, 1))]
    )
    session.add("Buy Milk")
    session.roll_over(NEXT_MORNING)
    assert len(session.reserve) == 1


def test_internal_spaces_are_not_normalised_for_the_dedup() -> None:
    session = session_on(D24)
    session.add("a  b")
    session.add("a b")
    session.roll_over(NEXT_MORNING)
    assert len(session.reserve) == 2


def test_an_unfinished_recurring_task_is_not_carried_to_the_reserve() -> None:
    daily = RecurringItem(text="water", weekdays=[0, 1, 2, 3, 4, 5, 6])
    session = session_on(D24, recurring=[daily])
    old_task = session.inject_recurring(D24.weekday())[0]
    session.roll_over(NEXT_MORNING)
    assert session.reserve == []
    assert [task.text for task in session.day.tasks] == ["water"]
    assert session.day.tasks[0].id != old_task.id


def test_a_struck_task_is_not_carried_to_the_reserve() -> None:
    session = session_on(D24)
    task = session.add("done deal")
    session.strike(task.id, now=STAMP)
    old = session.roll_over(NEXT_MORNING)
    assert session.reserve == []
    assert [task.text for task in old.tasks] == ["done deal"]


def test_a_deleted_reserve_task_does_not_return_to_the_reserve() -> None:
    session = session_on(D24)
    origin = session.add_to_reserve("regret", today=date(2026, 8, 18))
    task = session.draw_from_reserve(origin.id)
    session.delete(task.id, now=STAMP)
    old = session.roll_over(NEXT_MORNING)
    assert session.reserve == []
    assert len(old.deletions) == 1


def test_a_deleted_day_task_does_not_go_to_the_reserve() -> None:
    session = session_on(D24)
    session.add("keep me")
    gone = session.add("delete me")
    session.delete(gone.id, now=STAMP)
    session.roll_over(NEXT_MORNING)
    assert [item.text for item in session.reserve] == ["keep me"]


def test_the_counter_restarts_at_one() -> None:
    session = session_on(D24)
    for _ in range(5):
        session.add("x")
    session.roll_over(NEXT_MORNING)
    assert session.add("fresh").num == 1


def test_recurring_are_injected_for_the_new_days_weekday() -> None:
    session = session_on(D24)
    session.add_recurring("is due", [D25.weekday()])
    session.add_recurring("not due", [(D25.weekday() + 1) % 7])
    session.roll_over(NEXT_MORNING)
    assert [task.text for task in session.day.tasks] == ["is due"]
    assert session.day.tasks[0].origin == Origin.RECURRING


def test_multi_day_runs_once_and_lands_on_the_reference_date() -> None:
    session = session_on(D24)
    session.add("stale task")
    session.roll_over(datetime(2026, 8, 29, 9, 0))
    assert session.day.date == date(2026, 8, 29)
    assert [item.text for item in session.reserve] == ["stale task"]


def test_multi_day_archives_one_file_under_the_old_date(tmp_path: Path) -> None:
    session = session_on(D24)
    session.add("x")
    old = session.roll_over(datetime(2026, 8, 29, 9, 0))
    path = archive(old, data_dir=tmp_path)
    assert path.name == "2026-08-24.json"
    assert list((tmp_path / "archive").iterdir()) == [path]


def test_replayed_archive_leaves_a_single_file(tmp_path: Path) -> None:
    session = session_on(D24)
    session.add("x")
    old = session.roll_over(NEXT_MORNING)
    archive(old, data_dir=tmp_path)
    archive(old, data_dir=tmp_path)
    assert len(list((tmp_path / "archive").iterdir())) == 1


def test_a_list_filled_at_one_am_still_belongs_to_the_previous_day() -> None:
    assert session_on(D24).rollover_due(datetime(2026, 8, 25, 1, 0)) is False


def test_the_rollover_fires_after_four_am() -> None:
    session = session_on(D24)
    assert session.rollover_due(datetime(2026, 8, 25, 5, 0)) is True
    session.roll_over(datetime(2026, 8, 25, 5, 0))
    assert session.day.date == D25


# SPECIFICATION.md §2.5: the boundary follows local wall time "sans
# compensation". reference_date subtracts four hours from the naive
# components of an aware datetime, so a real DST zone must not shift the
# day it lands on.


def test_reference_date_across_the_autumn_fall_back() -> None:
    # 2026-10-25: 03:00 CEST winds back to 02:00 CET, so 03:30 happens
    # twice. Both foldings are before the 04:00 boundary; 04:30 is after.
    assert reference_date(
        datetime(2026, 10, 25, 3, 30, fold=0, tzinfo=PARIS_TZ)
    ) == date(2026, 10, 24)
    assert reference_date(
        datetime(2026, 10, 25, 3, 30, fold=1, tzinfo=PARIS_TZ)
    ) == date(2026, 10, 24)
    assert reference_date(datetime(2026, 10, 25, 4, 30, tzinfo=PARIS_TZ)) == date(
        2026, 10, 25
    )


def test_reference_date_across_the_spring_forward() -> None:
    # 2027-03-28: 02:00 CET jumps to 03:00 CEST. 03:30 (CEST) is still
    # before the 04:00 boundary; 04:30 is after.
    assert reference_date(datetime(2027, 3, 28, 3, 30, tzinfo=PARIS_TZ)) == date(
        2027, 3, 27
    )
    assert reference_date(datetime(2027, 3, 28, 4, 30, tzinfo=PARIS_TZ)) == date(
        2027, 3, 28
    )


def test_rollover_across_a_dst_transition_archives_exactly_one_day(
    tmp_path: Path,
) -> None:
    # Evening of 2026-10-24 (CEST) to the morning of 2026-10-25 (CET),
    # across the autumn fall-back: one archive, under the old date.
    session = session_on(date(2026, 10, 24))
    session.add("carry over")
    morning = datetime(2026, 10, 25, 10, 0, tzinfo=PARIS_TZ)
    assert session.rollover_due(morning) is True
    old = session.roll_over(morning)
    assert old.date == date(2026, 10, 24)
    assert session.day.date == date(2026, 10, 25)
    path = archive(old, data_dir=tmp_path)
    assert path.name == "2026-10-24.json"
    assert list((tmp_path / "archive").iterdir()) == [path]
