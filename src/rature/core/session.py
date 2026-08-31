# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""A day's state and the operations on it. Reads and writes no file."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from rature.core.models import Deletion, Origin, RecurringItem, ReserveItem, Task
from rature.core.recurrence import due_on


class LockedError(Exception):
    """An operation was refused because the list is frozen."""


def _now() -> datetime:
    return datetime.now().astimezone()


def reference_date(now: datetime) -> date:
    """The day a moment belongs to; the boundary is 04:00 local time."""
    return (now - timedelta(hours=4)).date()


def _norm(text: str) -> str:
    """Trim the ends and casefold; for the rollover duplicate check only."""
    return text.strip().casefold()


def _stamp(now: datetime | None) -> datetime:
    if now is None:
        return _now()
    if now.tzinfo is None:
        raise ValueError("now must carry a UTC offset")
    return now


@dataclass(kw_only=True)
class Day:
    """The counter, the lock, the tasks and the deletion journal of one day."""

    date: date
    counter: int = 1
    locked: bool = False
    tasks: list[Task] = field(default_factory=list)
    deletions: list[Deletion] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "counter": self.counter,
            "locked": self.locked,
            "tasks": [task.to_dict() for task in self.tasks],
            "deletions": [entry.to_dict() for entry in self.deletions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Day:
        return cls(
            date=date.fromisoformat(data["date"]),
            counter=data["counter"],
            locked=data["locked"],
            tasks=[Task.from_dict(task) for task in data["tasks"]],
            deletions=[Deletion.from_dict(entry) for entry in data["deletions"]],
        )


class Session:
    """Operations on a day, its reserve and its recurring templates."""

    def __init__(
        self,
        day: Day,
        *,
        reserve: list[ReserveItem] | None = None,
        recurring: list[RecurringItem] | None = None,
    ) -> None:
        self.day = day
        self.reserve = reserve if reserve is not None else []
        self.recurring = recurring if recurring is not None else []

    @property
    def struck(self) -> list[Task]:
        return [task for task in self.day.tasks if task.done]

    @property
    def active(self) -> list[Task]:
        return [task for task in self.day.tasks if not task.done]

    def view(self) -> list[Task]:
        """Display order: the struck block on top, then the active tasks."""
        return self.struck + self.active

    def _task(self, task_id: str) -> Task:
        for task in self.day.tasks:
            if task.id == task_id:
                return task
        raise KeyError(task_id)

    def add(self, text: str) -> Task:
        if self.day.locked:
            raise LockedError("the list is frozen")
        task = Task(num=self.day.counter, text=text, origin=Origin.DAY)
        self.day.counter += 1
        self.day.tasks.append(task)
        return task

    def strike(self, task_id: str, *, now: datetime | None = None) -> None:
        task = self._task(task_id)
        if task.done:
            raise ValueError(f"task {task.num} is already struck")
        task.done = True
        task.done_at = _stamp(now)

    def unstrike(self, task_id: str) -> None:
        task = self._task(task_id)
        if not task.done:
            raise ValueError(f"task {task.num} is not struck")
        task.done = False
        task.done_at = None

    def rename(self, task_id: str, text: str) -> None:
        self._task(task_id).text = text

    def delete(self, task_id: str, *, now: datetime | None = None) -> None:
        task = self._task(task_id)
        self.day.deletions.append(
            Deletion(
                id=task.id,
                num=task.num,
                text=task.text,
                origin=task.origin,
                source_id=task.source_id,
                deleted_at=_stamp(now),
            )
        )
        self.day.tasks.remove(task)

    def reorder(self, ordered_ids: list[str]) -> None:
        by_id = {task.id: task for task in self.day.tasks}
        if len(ordered_ids) != len(by_id) or set(ordered_ids) != set(by_id):
            raise ValueError("reorder needs a permutation of the current task ids")
        self.day.tasks = [by_id[task_id] for task_id in ordered_ids]

    def lock(self) -> None:
        self.day.locked = True

    def unlock(self) -> None:
        self.day.locked = False

    def _reserve_item(self, item_id: str) -> ReserveItem:
        for item in self.reserve:
            if item.id == item_id:
                return item
        raise KeyError(item_id)

    def add_to_reserve(self, text: str, *, today: date) -> ReserveItem:
        # SPECIFICATION.md §2.7.4: manual reserve entries are never de-duplicated.
        item = ReserveItem(text=text, created=today)
        self.reserve.append(item)
        return item

    def rename_reserve(self, item_id: str, text: str) -> None:
        self._reserve_item(item_id).text = text

    def delete_from_reserve(self, item_id: str) -> None:
        self.reserve.remove(self._reserve_item(item_id))

    def draw_from_reserve(self, item_id: str) -> Task:
        if self.day.locked:
            raise LockedError("the list is frozen")
        item = self._reserve_item(item_id)
        # SPECIFICATION.md §2.5: a move, not a copy; source_id links back.
        task = Task(
            num=self.day.counter,
            text=item.text,
            origin=Origin.RESERVE,
            source_id=item.id,
            source_created=item.created,
        )
        self.day.counter += 1
        self.day.tasks.append(task)
        self.reserve.remove(item)
        return task

    def _recurring_item(self, item_id: str) -> RecurringItem:
        for item in self.recurring:
            if item.id == item_id:
                return item
        raise KeyError(item_id)

    def add_recurring(self, text: str, weekdays: list[int]) -> RecurringItem:
        item = RecurringItem(text=text, weekdays=list(weekdays))
        self.recurring.append(item)
        return item

    def edit_recurring(
        self,
        item_id: str,
        *,
        text: str | None = None,
        weekdays: list[int] | None = None,
    ) -> RecurringItem:
        old = self._recurring_item(item_id)
        new = RecurringItem(
            id=old.id,
            text=old.text if text is None else text,
            weekdays=list(old.weekdays if weekdays is None else weekdays),
        )
        self.recurring[self.recurring.index(old)] = new
        return new

    def delete_recurring(self, item_id: str) -> None:
        self.recurring.remove(self._recurring_item(item_id))

    def inject_recurring(self, weekday: int) -> list[Task]:
        if self.day.locked:
            raise LockedError("the list is frozen")
        created: list[Task] = []
        for template in due_on(weekday, self.recurring):
            task = Task(
                num=self.day.counter,
                text=template.text,
                origin=Origin.RECURRING,
                template_id=template.id,
            )
            self.day.counter += 1
            self.day.tasks.append(task)
            created.append(task)
        return created

    def rollover_due(self, now: datetime) -> bool:
        return reference_date(now) > self.day.date

    def roll_over(self, now: datetime) -> Day:
        """Run the SPECIFICATION.md §2.5 rollover; archive the old day, then save."""
        if not self.rollover_due(now):
            raise ValueError("no rollover is due")
        old = self.day
        new_date = reference_date(now)
        for task in old.tasks:
            if not task.done and task.origin == Origin.RESERVE:
                self.reserve.append(
                    ReserveItem(
                        id=task.source_id,
                        text=task.text,
                        created=task.source_created,
                    )
                )
        seen = {_norm(item.text) for item in self.reserve}
        for task in old.tasks:
            if not task.done and task.origin == Origin.DAY:
                key = _norm(task.text)
                if key not in seen:
                    self.reserve.append(ReserveItem(text=task.text, created=new_date))
                    seen.add(key)
        self.day = Day(date=new_date)
        self.inject_recurring(new_date.weekday())
        return old
