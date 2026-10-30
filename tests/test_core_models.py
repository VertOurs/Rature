# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Serialisation round-trips and the validation the models enforce."""

from datetime import date, datetime, timedelta, timezone

import pytest

from rature.core.models import (
    Deletion,
    Origin,
    PreparedTask,
    RecurringItem,
    ReserveItem,
    ReserveSource,
    Task,
)

PARIS = timezone(timedelta(hours=2))
STAMP = datetime(2026, 8, 24, 14, 32, 7, tzinfo=PARIS)


def test_active_task_round_trips() -> None:
    task = Task(num=1, text="write the tests", origin=Origin.DAY)
    assert Task.from_dict(task.to_dict()) == task


def test_struck_task_round_trips_and_keeps_the_offset() -> None:
    task = Task(num=4, text="done thing", origin=Origin.DAY, done=True, done_at=STAMP)
    assert task.to_dict()["done_at"] == "2026-08-24T14:32:07+02:00"
    assert Task.from_dict(task.to_dict()) == task


def test_task_rejects_a_naive_done_at() -> None:
    with pytest.raises(ValueError):
        Task(
            num=1,
            text="x",
            origin=Origin.DAY,
            done=True,
            done_at=datetime(2026, 8, 24, 14, 32, 7),
        )


def test_task_rejects_done_without_a_timestamp() -> None:
    with pytest.raises(ValueError):
        Task(num=1, text="x", origin=Origin.DAY, done=True)


def test_task_rejects_a_timestamp_without_done() -> None:
    with pytest.raises(ValueError):
        Task(num=1, text="x", origin=Origin.DAY, done=False, done_at=STAMP)


def test_origin_serialises_as_a_plain_string() -> None:
    task = Task(
        num=7,
        text="from reserve",
        origin=Origin.RESERVE,
        source=ReserveSource(id="abc", created=date(2026, 8, 20)),
    )
    assert task.to_dict()["origin"] == "reserve"


SOURCE = ReserveSource(id="abc", created=date(2026, 8, 20))


def test_reserve_task_rejects_a_missing_source() -> None:
    with pytest.raises(ValueError):
        Task(num=1, text="x", origin=Origin.RESERVE)


@pytest.mark.parametrize("origin", [Origin.DAY, Origin.RECURRING])
def test_a_task_not_from_the_reserve_rejects_a_source(origin: Origin) -> None:
    with pytest.raises(ValueError):
        Task(num=1, text="x", origin=origin, source=SOURCE)


def test_source_serialises_as_the_two_flat_keys_of_version_1() -> None:
    data = Task(num=1, text="x", origin=Origin.RESERVE, source=SOURCE).to_dict()
    assert (data["source_id"], data["source_created"]) == ("abc", "2026-08-20")
    assert "source" not in data


def test_no_source_serialises_as_two_nulls() -> None:
    data = Task(num=1, text="x", origin=Origin.DAY).to_dict()
    assert (data["source_id"], data["source_created"]) == (None, None)


@pytest.mark.parametrize(
    "half", [{"source_id": None}, {"source_created": None}], ids=["id", "created"]
)
def test_a_half_source_on_disk_is_refused(half: dict) -> None:
    data = Task(num=1, text="x", origin=Origin.RESERVE, source=SOURCE).to_dict()
    with pytest.raises(ValueError, match="go together"):
        Task.from_dict(data | half)


def test_cryptic_text_is_stored_verbatim() -> None:
    task = Task(num=1, text="  MTG w/ P re: Q3  ", origin=Origin.DAY)
    assert Task.from_dict(task.to_dict()).text == "  MTG w/ P re: Q3  "


def test_source_created_round_trips() -> None:
    task = Task(
        num=3,
        text="drawn",
        origin=Origin.RESERVE,
        source=ReserveSource(id="r1", created=date(2026, 8, 20)),
    )
    restored = Task.from_dict(task.to_dict())
    assert restored.source.created == date(2026, 8, 20)
    assert restored == task


def test_prepared_task_round_trips() -> None:
    task = PreparedTask(text="book the train", origin=Origin.DAY)
    assert PreparedTask.from_dict(task.to_dict()) == task


def test_prepared_task_from_the_reserve_round_trips_with_its_priority() -> None:
    task = PreparedTask(
        text="call the insurance",
        origin=Origin.RESERVE,
        source=ReserveSource(id="r1", created=date(2026, 8, 20)),
        priority=True,
    )
    data = task.to_dict()
    assert data["origin"] == "reserve"
    assert data["source_created"] == "2026-08-20"
    assert PreparedTask.from_dict(data) == task


def test_prepared_task_has_no_number_and_no_strike() -> None:
    data = PreparedTask(text="x", origin=Origin.DAY).to_dict()
    assert {"num", "done", "done_at"}.isdisjoint(data)


def test_prepared_task_rejects_a_recurring_origin() -> None:
    with pytest.raises(ValueError):
        PreparedTask(text="x", origin=Origin.RECURRING)


def test_prepared_reserve_task_rejects_a_missing_source() -> None:
    with pytest.raises(ValueError):
        PreparedTask(text="x", origin=Origin.RESERVE)


def test_prepared_day_task_rejects_a_source() -> None:
    with pytest.raises(ValueError):
        PreparedTask(text="x", origin=Origin.DAY, source=SOURCE)


def test_reserve_item_round_trips_with_a_plain_date() -> None:
    item = ReserveItem(text="someday thing", created=date(2026, 8, 20))
    assert item.to_dict()["created"] == "2026-08-20"
    assert ReserveItem.from_dict(item.to_dict()) == item


def test_recurring_item_round_trips() -> None:
    item = RecurringItem(text="water plants", weekdays=[0, 3])
    assert RecurringItem.from_dict(item.to_dict()) == item


def test_recurring_item_accepts_every_day() -> None:
    assert RecurringItem(text="daily", weekdays=[0, 1, 2, 3, 4, 5, 6]).weekdays == [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_recurring_item_rejects_empty_weekdays() -> None:
    with pytest.raises(ValueError):
        RecurringItem(text="broken", weekdays=[])


def test_recurring_item_rejects_a_weekday_out_of_range() -> None:
    with pytest.raises(ValueError):
        RecurringItem(text="broken", weekdays=[0, 7])


def test_every_other_week_recurring_item_round_trips() -> None:
    item = RecurringItem(
        text="swimming", weekdays=[1], every_other_week_from=date(2026, 12, 21)
    )
    assert item.to_dict()["every_other_week_from"] == "2026-12-21"
    assert RecurringItem.from_dict(item.to_dict()) == item


def test_a_weekly_recurring_item_stores_a_null_start() -> None:
    item = RecurringItem(text="water plants", weekdays=[0])
    assert item.to_dict()["every_other_week_from"] is None


def test_recurring_item_rejects_a_start_that_is_not_a_monday() -> None:
    with pytest.raises(ValueError, match="Monday"):
        RecurringItem(
            text="broken", weekdays=[1], every_other_week_from=date(2026, 12, 22)
        )


def test_deletion_round_trips() -> None:
    entry = Deletion(
        id="task-uuid",
        num=4,
        text="abandoned",
        origin=Origin.DAY,
        deleted_at=STAMP,
        index=1,
    )
    assert Deletion.from_dict(entry.to_dict()) == entry


def test_deletion_round_trips_with_every_field_set() -> None:
    entry = Deletion(
        id="task-uuid",
        num=7,
        text="drawn and struck",
        origin=Origin.RESERVE,
        deleted_at=STAMP,
        index=2,
        source=ReserveSource(id="r1", created=date(2026, 8, 20)),
        template_id="tmpl-1",
        done=True,
        done_at=STAMP,
    )
    restored = Deletion.from_dict(entry.to_dict())
    assert restored == entry
    assert restored.source.created == date(2026, 8, 20)
    assert restored.done_at == STAMP


def test_deletion_rejects_a_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        Deletion(
            id="task-uuid",
            num=4,
            text="abandoned",
            origin=Origin.DAY,
            deleted_at=datetime(2026, 8, 24, 14, 32, 7),
            index=0,
        )


def test_deletion_rejects_done_without_a_timestamp() -> None:
    with pytest.raises(ValueError):
        Deletion(
            id="task-uuid",
            num=4,
            text="abandoned",
            origin=Origin.DAY,
            deleted_at=STAMP,
            index=0,
            done=True,
        )


def test_deletion_rejects_a_timestamp_without_done() -> None:
    with pytest.raises(ValueError):
        Deletion(
            id="task-uuid",
            num=4,
            text="abandoned",
            origin=Origin.DAY,
            deleted_at=STAMP,
            index=0,
            done=False,
            done_at=STAMP,
        )


def test_generated_ids_are_unique() -> None:
    assert (
        Task(num=1, text="a", origin=Origin.DAY).id
        != Task(num=2, text="b", origin=Origin.DAY).id
    )


def test_only_an_active_non_recurring_task_can_go_back_to_reserve() -> None:
    day = Task(num=1, text="t", origin=Origin.DAY)
    reserve = Task(
        num=2,
        text="t",
        origin=Origin.RESERVE,
        source=ReserveSource(id="r", created=date(2026, 8, 1)),
    )
    recurring = Task(num=3, text="t", origin=Origin.RECURRING, template_id="x")
    struck = Task(num=4, text="t", origin=Origin.DAY, done=True, done_at=STAMP)
    assert day.can_go_back_to_reserve
    assert reserve.can_go_back_to_reserve
    assert not recurring.can_go_back_to_reserve
    assert not struck.can_go_back_to_reserve
