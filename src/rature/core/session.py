# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""A day's state and the operations on it. Reads and writes no file."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from rature.core.models import (
    Deletion,
    Origin,
    PreparedTask,
    RecurringItem,
    ReserveItem,
    Task,
)
from rature.core.recurrence import Cadence, due_on, start_monday


class LockedError(Exception):
    """An operation was refused because the list is frozen."""


def reference_date(now: datetime) -> date:
    """The day a moment belongs to; the boundary is 04:00 local time."""
    return (now - timedelta(hours=4)).date()


def _norm(text: str) -> str:
    """Trim the ends and casefold; for the rollover duplicate check only."""
    return text.strip().casefold()


def _stamp(now: datetime) -> datetime:
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
        tomorrow: list[PreparedTask] | None = None,
        recurring: list[RecurringItem] | None = None,
    ) -> None:
        self.day = day
        self.reserve = reserve if reserve is not None else []
        self.tomorrow = tomorrow if tomorrow is not None else []
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

    def add_struck(self, text: str, *, now: datetime) -> Task:
        """Add a task already struck: SPECIFICATION.md §2.4's retroactive
        logging in one gesture instead of add then strike.

        Same as add() plus an immediate strike; view() lifts it into the
        struck block. Refused on a frozen list, like any add (§2.1
        point 3).
        """
        if self.day.locked:
            raise LockedError("the list is frozen")
        task = Task(
            num=self.day.counter,
            text=text,
            origin=Origin.DAY,
            done=True,
            done_at=_stamp(now),
        )
        self.day.counter += 1
        self.day.tasks.append(task)
        return task

    def strike(self, task_id: str, *, now: datetime) -> None:
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

    def set_priority(self, task_id: str, priority: bool) -> None:
        """Mark or unmark a task. SPECIFICATION.md §2.5: a marker only.

        Never touches the order or the number. Allowed on a frozen list
        and on a struck task, like a rename (§2.1 point 3).
        """
        self._task(task_id).priority = priority

    def delete(self, task_id: str, *, now: datetime) -> None:
        task = self._task(task_id)
        index = self.day.tasks.index(task)
        self.day.deletions.append(
            Deletion(
                id=task.id,
                num=task.num,
                text=task.text,
                origin=task.origin,
                source_id=task.source_id,
                source_created=task.source_created,
                template_id=task.template_id,
                done=task.done,
                done_at=task.done_at,
                priority=task.priority,
                index=index,
                deleted_at=_stamp(now),
            )
        )
        self.day.tasks.remove(task)

    def undo_last_deletion(self) -> Task:
        """Restore the most recently deleted task and drop its journal entry.

        SPECIFICATION.md §3.2: the task reappears at its recorded index
        with its original number, struck iff it was struck. The entry
        leaves the journal so the §2.6 count stays exact (ADR 0005). The
        index is clamped: adds, other deletes or a reorder since may have
        left no slot at the original position. The counter is untouched,
        so the freed number is still never reused (§2.4).
        """
        if not self.day.deletions:
            raise ValueError("no deletion to undo")
        entry = self.day.deletions.pop()
        task = Task(
            id=entry.id,
            num=entry.num,
            text=entry.text,
            origin=entry.origin,
            done=entry.done,
            done_at=entry.done_at,
            source_id=entry.source_id,
            source_created=entry.source_created,
            template_id=entry.template_id,
            priority=entry.priority,
        )
        self.day.tasks.insert(min(entry.index, len(self.day.tasks)), task)
        return task

    def reorder(self, ordered_ids: list[str]) -> None:
        by_id = {task.id: task for task in self.day.tasks}
        if len(ordered_ids) != len(by_id) or set(ordered_ids) != set(by_id):
            raise ValueError("reorder needs a permutation of the current task ids")
        self.day.tasks = [by_id[task_id] for task_id in ordered_ids]

    def move_before(self, task_id: str, target_id: str | None) -> None:
        """Reorder day.tasks so task_id sits right before target_id.

        target_id=None moves the task to the end of day.tasks. task_id
        == target_id is a silent no-op: a drag-and-drop that drops a
        row back where it was picked up.

        day.tasks only orders the display within its own block: view()
        always puts the struck tasks above the active ones. Moving an
        active task "before" a struck one has no visible effect until
        it is struck too.
        """
        self.day.tasks = _moved_before(self.day.tasks, task_id, target_id)

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

    def set_reserve_priority(self, item_id: str, priority: bool) -> None:
        """Mark or unmark a reserve item; never moves it (§2.5)."""
        self._reserve_item(item_id).priority = priority

    def delete_from_reserve(self, item_id: str) -> None:
        self.reserve.remove(self._reserve_item(item_id))

    def move_reserve_before(self, item_id: str, target_id: str | None) -> None:
        """Reorder the reserve so item_id sits right before target_id.

        SPECIFICATION.md §2.5 and §3.3: same rule as move_before,
        target_id=None moves the item to the end. Allowed on a frozen day,
        which only stops the day's composition.
        """
        self.reserve = _moved_before(self.reserve, item_id, target_id)

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
            priority=item.priority,
        )
        self.day.counter += 1
        self.day.tasks.append(task)
        self.reserve.remove(item)
        return task

    def send_to_reserve(self, task_id: str, *, today: date) -> ReserveItem:
        """Move an active task back to the end of the reserve.

        SPECIFICATION.md §2.5's manual send-back: the draw in reverse.
        Allowed on a frozen list, like a delete; refused where
        Task.can_go_back_to_reserve says so. The task
        leaves no trace in the day and its number is never reused.
        """
        task = self._task(task_id)
        if not task.can_go_back_to_reserve:
            raise ValueError(f"task {task.num} cannot go back to the reserve")
        item = _returning_item(task, today)
        self.day.tasks.remove(task)
        self.reserve.append(item)
        return item

    # The Tomorrow list, SPECIFICATION.md §2.5. Nothing here checks
    # day.locked: freezing the day stops its composition, and Tomorrow is
    # not the day.

    def _prepared(self, task_id: str) -> PreparedTask:
        for task in self.tomorrow:
            if task.id == task_id:
                return task
        raise KeyError(task_id)

    def add_to_tomorrow(self, text: str) -> PreparedTask:
        # SPECIFICATION.md §2.5: never de-duplicated, an explicit gesture.
        task = PreparedTask(text=text, origin=Origin.DAY)
        self.tomorrow.append(task)
        return task

    def rename_tomorrow(self, task_id: str, text: str) -> None:
        self._prepared(task_id).text = text

    def set_tomorrow_priority(self, task_id: str, priority: bool) -> None:
        """Mark or unmark a prepared task; never moves it (§2.5)."""
        self._prepared(task_id).priority = priority

    def delete_from_tomorrow(self, task_id: str) -> None:
        """Remove a prepared task for good, SPECIFICATION.md §2.7.9.

        No journal entry and no undo: the journal belongs to the day. A task
        drawn from the reserve takes its original item with it (§2.7.3).
        """
        self.tomorrow.remove(self._prepared(task_id))

    def move_tomorrow_before(self, task_id: str, target_id: str | None) -> None:
        """Reorder Tomorrow with move_before's rule (SPECIFICATION.md §3.16)."""
        self.tomorrow = _moved_before(self.tomorrow, task_id, target_id)

    def move_to_tomorrow(self, task_id: str) -> PreparedTask:
        """Move an active day task to the end of Tomorrow, SPECIFICATION.md §2.5.

        Same restrictions as send_to_reserve and allowed on a frozen list
        like it. The task keeps its id, origin, reserve link and priority,
        loses its number, and leaves no trace in the day.
        """
        task = self._task(task_id)
        if not task.can_go_back_to_reserve:
            raise ValueError(f"task {task.num} cannot move to tomorrow")
        prepared = PreparedTask(
            id=task.id,
            text=task.text,
            origin=task.origin,
            source_id=task.source_id,
            source_created=task.source_created,
            priority=task.priority,
        )
        self.day.tasks.remove(task)
        self.tomorrow.append(prepared)
        return prepared

    def move_reserve_to_tomorrow(self, item_id: str) -> PreparedTask:
        """Move a reserve item to the end of Tomorrow, SPECIFICATION.md §2.5.

        A move like draw_from_reserve, linked back by source_id, but allowed
        on a frozen day.
        """
        item = self._reserve_item(item_id)
        prepared = PreparedTask(
            text=item.text,
            origin=Origin.RESERVE,
            source_id=item.id,
            source_created=item.created,
            priority=item.priority,
        )
        self.reserve.remove(item)
        self.tomorrow.append(prepared)
        return prepared

    def move_to_today(self, task_id: str) -> Task:
        """Bring a prepared task to the end of the day, SPECIFICATION.md §2.5.

        Refused on a frozen list, like a draw. The task gets the next number
        and keeps its id, origin, reserve link and priority.
        """
        if self.day.locked:
            raise LockedError("the list is frozen")
        prepared = self._prepared(task_id)
        task = self._enter_day(prepared)
        self.tomorrow.remove(prepared)
        return task

    def _enter_day(self, prepared: PreparedTask) -> Task:
        """Append ``prepared`` to the day with the next number.

        Shared by move_to_today and the rollover's step 7: same id, origin,
        reserve link and priority. Leaves Tomorrow to the caller.
        """
        task = Task(
            id=prepared.id,
            num=self.day.counter,
            text=prepared.text,
            origin=prepared.origin,
            source_id=prepared.source_id,
            source_created=prepared.source_created,
            priority=prepared.priority,
        )
        self.day.counter += 1
        self.day.tasks.append(task)
        return task

    def send_tomorrow_to_reserve(self, task_id: str, *, today: date) -> ReserveItem:
        """Move a prepared task to the end of the reserve, like send_to_reserve."""
        prepared = self._prepared(task_id)
        item = _returning_item(prepared, today)
        self.tomorrow.remove(prepared)
        self.reserve.append(item)
        return item

    def _recurring_item(self, item_id: str) -> RecurringItem:
        for item in self.recurring:
            if item.id == item_id:
                return item
        raise KeyError(item_id)

    def add_recurring(
        self,
        text: str,
        weekdays: list[int],
        *,
        cadence: Cadence = Cadence.WEEKLY,
        today: date | None = None,
    ) -> RecurringItem:
        """Append a template. ``today`` is required for every other week."""
        item = RecurringItem(
            text=text,
            weekdays=list(weekdays),
            every_other_week_from=start_monday(cadence, today),
        )
        self.recurring.append(item)
        return item

    def edit_recurring(
        self,
        item_id: str,
        *,
        text: str | None = None,
        weekdays: list[int] | None = None,
        cadence: Cadence | None = None,
        today: date | None = None,
    ) -> RecurringItem:
        """Replace the fields given; None keeps the current value."""
        old = self._recurring_item(item_id)
        start = old.every_other_week_from
        if cadence is not None:
            start = start_monday(cadence, today, start)
        new = RecurringItem(
            id=old.id,
            text=old.text if text is None else text,
            weekdays=list(old.weekdays if weekdays is None else weekdays),
            every_other_week_from=start,
        )
        self.recurring[self.recurring.index(old)] = new
        return new

    def delete_recurring(self, item_id: str) -> None:
        self.recurring.remove(self._recurring_item(item_id))

    def inject_recurring(self, day: date) -> list[Task]:
        if self.day.locked:
            raise LockedError("the list is frozen")
        created: list[Task] = []
        for template in due_on(day, self.recurring):
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
        """Run the SPECIFICATION.md §2.5 rollover, seven steps, return the old day.

        Archiving it and saving the new one is the caller's job; App.ensure_day
        is where that full sequence lives.
        """
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
                        priority=task.priority,
                    )
                )
        # The first item per normalised text: the one a duplicate is
        # compared against, and the one it hands its priority to
        # (SPECIFICATION.md §2.7.8).
        seen: dict[str, ReserveItem] = {}
        for item in self.reserve:
            seen.setdefault(_norm(item.text), item)
        for task in old.tasks:
            if not task.done and task.origin == Origin.DAY:
                key = _norm(task.text)
                if key in seen:
                    if task.priority:
                        seen[key].priority = True
                    continue
                item = ReserveItem(
                    text=task.text, created=new_date, priority=task.priority
                )
                self.reserve.append(item)
                seen[key] = item
        self.day = Day(date=new_date)
        self.inject_recurring(new_date)
        # Step 7: the prepared list enters the new day after the recurring
        # tasks, as if dictated first thing. Numbers are given here (§2.4).
        for prepared in self.tomorrow:
            self._enter_day(prepared)
        self.tomorrow = []
        return old


def _returning_item(task: Task | PreparedTask, today: date) -> ReserveItem:
    """The reserve item a task becomes when sent back by hand (§2.5).

    Shared by send_to_reserve and send_tomorrow_to_reserve.
    """
    if task.origin == Origin.RESERVE:
        # Same as the rollover's point 2: the original item comes back,
        # renamed text included (SPECIFICATION.md §2.7.1).
        return ReserveItem(
            id=task.source_id,
            text=task.text,
            created=task.source_created,
            priority=task.priority,
        )
    # SPECIFICATION.md §2.7.4: an explicit gesture, never de-duplicated,
    # unlike the rollover's point 3.
    return ReserveItem(text=task.text, created=today, priority=task.priority)


def _moved_before[T: (Task, ReserveItem, PreparedTask)](
    items: list[T], item_id: str, target_id: str | None
) -> list[T]:
    """items with item_id moved right before target_id, or to the end on None.

    The one rule behind Session.move_before, move_reserve_before and
    move_tomorrow_before.
    item_id == target_id returns the list unchanged: a drag-and-drop that
    drops a row back where it was picked up. Unknown ids raise KeyError.
    """
    by_id = {item.id: item for item in items}
    moving = by_id[item_id]
    if item_id == target_id:
        return items
    rest = [item for item in items if item.id != item_id]
    if target_id is None:
        return [*rest, moving]
    if target_id not in by_id:
        raise KeyError(target_id)
    index = [item.id for item in rest].index(target_id)
    return [*rest[:index], moving, *rest[index:]]
