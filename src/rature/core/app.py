# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Coordinates a Session with storage behind a single injectable clock.

No gi import: this is what a graphical interface calls into, never the
other way around.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from rature.core import storage
from rature.core.models import RecurringItem, ReserveItem, Task
from rature.core.session import Day, Session, reference_date
from rature.core.storage import Store


class StartupOutcome(enum.Enum):
    """What App.open had to do to produce a ready App.

    A file newer than this build supports has no place here: it raises
    migrations.FutureVersionError straight out of open(), and no App is
    built at all, so the interface never has to handle a half-valid one.
    """

    LOADED = enum.auto()
    FIRST_LAUNCH = enum.auto()
    RECOVERED_FROM_CORRUPTION = enum.auto()


def _default_clock() -> datetime:
    return datetime.now().astimezone()


class App:
    """Coordinates a Session with storage, behind a single injectable clock.

    A save failure in the middle of a mutation raises, and the in-memory
    Session mutation it followed is not rolled back. Undoing it would need
    a snapshot and restore around every mutation, harder to get right than
    it looks, for a failure mode (disk I/O erroring mid-write) that already
    surfaces immediately as a raised exception the caller cannot silently
    ignore.
    """

    def __init__(
        self,
        *,
        data_dir: Path,
        session: Session,
        clock: Callable[[], datetime],
        startup: StartupOutcome,
    ) -> None:
        self.data_dir = data_dir
        self.session = session
        self.clock = clock
        self.startup = startup

    @classmethod
    def open(
        cls,
        data_dir: Path | None = None,
        *,
        clock: Callable[[], datetime] = _default_clock,
    ) -> App:
        """Load or create the data file, then catch up on any due rollover.

        Returns an App whose day already matches the current reference
        date (SPECIFICATION.md §2.5): the caller never has to know a
        rollover happened, let alone run it itself.
        """
        resolved_dir = data_dir if data_dir is not None else storage.xdg_data_dir()
        now = clock()
        try:
            store = storage.load(data_dir=resolved_dir)
        except FileNotFoundError:
            app = cls._bootstrap(resolved_dir, clock, now, StartupOutcome.FIRST_LAUNCH)
        except (ValueError, KeyError, TypeError):
            storage.quarantine(now, data_dir=resolved_dir)
            app = cls._bootstrap(
                resolved_dir, clock, now, StartupOutcome.RECOVERED_FROM_CORRUPTION
            )
        else:
            app = cls(
                data_dir=resolved_dir,
                session=store.into_session(),
                clock=clock,
                startup=StartupOutcome.LOADED,
            )
        app.ensure_day()
        return app

    @classmethod
    def _bootstrap(
        cls,
        data_dir: Path,
        clock: Callable[[], datetime],
        now: datetime,
        startup: StartupOutcome,
    ) -> App:
        session = Session(Day(date=reference_date(now)))
        storage.save(Store.from_session(session), data_dir=data_dir)
        return cls(data_dir=data_dir, session=session, clock=clock, startup=startup)

    def ensure_day(self) -> Day | None:
        """Run the SPECIFICATION.md §2.5 rollover if due, as a single step.

        roll_over, archive, then save, in that order, so this sequence is
        never again something a caller has to remember. Returns the day
        that was archived, or None if none was due, so the caller knows
        whether it needs to refresh.
        """
        now = self.clock()
        if not self.session.rollover_due(now):
            return None
        old_day = self.session.roll_over(now)
        storage.archive(old_day, data_dir=self.data_dir)
        self._save()
        return old_day

    def archives(self) -> list[date]:
        """Dates with an archived day, most recent first."""
        return storage.list_archives(data_dir=self.data_dir)

    def read_archive(self, day_date: date) -> Day:
        """Load one archived day. See storage.load_archive for what can raise."""
        return storage.load_archive(day_date, data_dir=self.data_dir)

    def _save(self) -> None:
        storage.save(Store.from_session(self.session), data_dir=self.data_dir)

    # Mutations below wrap the matching Session method: supply now/today
    # from self.clock() where the operation needs one, then save. Business
    # errors (LockedError, KeyError, ValueError) come straight from Session
    # and are not caught here.

    def add(self, text: str) -> Task:
        task = self.session.add(text)
        self._save()
        return task

    def strike(self, task_id: str) -> None:
        self.session.strike(task_id, now=self.clock())
        self._save()

    def unstrike(self, task_id: str) -> None:
        self.session.unstrike(task_id)
        self._save()

    def rename(self, task_id: str, text: str) -> None:
        self.session.rename(task_id, text)
        self._save()

    def delete(self, task_id: str) -> None:
        self.session.delete(task_id, now=self.clock())
        self._save()

    def move_before(self, task_id: str, target_id: str | None) -> None:
        self.session.move_before(task_id, target_id)
        self._save()

    def lock(self) -> None:
        self.session.lock()
        self._save()

    def unlock(self) -> None:
        self.session.unlock()
        self._save()

    def add_to_reserve(self, text: str) -> ReserveItem:
        item = self.session.add_to_reserve(text, today=reference_date(self.clock()))
        self._save()
        return item

    def rename_reserve(self, item_id: str, text: str) -> None:
        self.session.rename_reserve(item_id, text)
        self._save()

    def delete_from_reserve(self, item_id: str) -> None:
        self.session.delete_from_reserve(item_id)
        self._save()

    def draw_from_reserve(self, item_id: str) -> Task:
        task = self.session.draw_from_reserve(item_id)
        self._save()
        return task

    def add_recurring(self, text: str, weekdays: list[int]) -> RecurringItem:
        item = self.session.add_recurring(text, weekdays)
        self._save()
        return item

    def edit_recurring(
        self,
        item_id: str,
        *,
        text: str | None = None,
        weekdays: list[int] | None = None,
    ) -> RecurringItem:
        item = self.session.edit_recurring(item_id, text=text, weekdays=weekdays)
        self._save()
        return item

    def delete_recurring(self, item_id: str) -> None:
        self.session.delete_recurring(item_id)
        self._save()
