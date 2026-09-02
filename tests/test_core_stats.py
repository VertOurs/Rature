# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Per-day archive counters for the Statistics window (SPECIFICATION.md §3.14)."""

from datetime import date, datetime, timedelta, timezone

from rature.core.models import Deletion, Origin, Task
from rature.core.session import Day
from rature.core.stats import DayCounts, day_counts

PARIS = timezone(timedelta(hours=2))
STAMP = datetime(2026, 8, 24, 12, 0, tzinfo=PARIS)


def _task(num: int, *, done: bool = False, origin: Origin = Origin.DAY) -> Task:
    reserve = origin is Origin.RESERVE
    return Task(
        num=num,
        text=f"task {num}",
        origin=origin,
        done=done,
        done_at=STAMP if done else None,
        source_id="src" if reserve else None,
        source_created=date(2026, 8, 1) if reserve else None,
    )


def _deletion(num: int) -> Deletion:
    return Deletion(
        id=f"d{num}",
        num=num,
        text=f"gone {num}",
        origin=Origin.DAY,
        deleted_at=STAMP,
        index=0,
    )


def _day(*, tasks=(), deletions=()) -> Day:
    return Day(date=date(2026, 8, 24), tasks=list(tasks), deletions=list(deletions))


def test_an_empty_day_is_all_zeros() -> None:
    assert day_counts(_day()) == DayCounts(added=0, struck=0, deleted=0, to_reserve=0)


def test_added_counts_tasks_plus_deletion_entries() -> None:
    day = _day(
        tasks=[_task(1), _task(2), _task(3)],
        deletions=[_deletion(4), _deletion(5)],
    )
    assert day_counts(day).added == 5


def test_struck_counts_done_tasks_and_ignores_deletions() -> None:
    day = _day(
        tasks=[_task(1, done=True), _task(2, done=True), _task(3)],
        deletions=[_deletion(4)],
    )
    assert day_counts(day).struck == 2


def test_deleted_counts_journal_entries() -> None:
    day = _day(tasks=[_task(1)], deletions=[_deletion(2), _deletion(3)])
    assert day_counts(day).deleted == 2


def test_to_reserve_is_unfinished_non_recurring_tasks() -> None:
    day = _day(
        tasks=[
            _task(1, origin=Origin.DAY),  # counts
            _task(2, origin=Origin.RESERVE),  # counts
            _task(3, origin=Origin.RECURRING),  # excluded: recurring
            _task(4, done=True, origin=Origin.DAY),  # excluded: done
        ]
    )
    assert day_counts(day).to_reserve == 2


def test_counts_are_independent_not_a_partition() -> None:
    day = _day(
        tasks=[
            _task(1, done=True),
            _task(2, done=True),
            _task(3),
            _task(4, origin=Origin.RECURRING),
        ],
        deletions=[_deletion(5)],
    )
    counts = day_counts(day)
    assert counts == DayCounts(added=5, struck=2, deleted=1, to_reserve=1)
