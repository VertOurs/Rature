# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Coordinates a Session with storage behind a single injectable clock.

No gi import: this is what a graphical interface calls into, never the
other way around.
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple

from rature.core import export, recurrence, search, stats, storage
from rature.core.migrations import FutureVersionError
from rature.core.models import PreparedTask, RecurringItem, ReserveItem, Task

# Cadence is part of this module's interface: ui/ may only import
# rature.core.app, and the recurring wrappers below take it as is.
from rature.core.recurrence import Cadence

# LockedError re-exported: ui/ may only import rature.core.app, and its
# mutation wrappers below raise it straight from Session.
from rature.core.session import Day, LockedError, Session, reference_date  # noqa: F401
from rature.core.storage import Store

_logger = logging.getLogger(__name__)


class StartupOutcome(enum.Enum):
    """How a ready App came to be.

    A file newer than this build supports has no place here: it raises
    migrations.FutureVersionError straight out of open(), and no App is
    built at all, so the interface never has to handle a half-valid one.
    The same goes for an unreadable or missing data file, see below.
    """

    LOADED = enum.auto()
    FIRST_LAUNCH = enum.auto()
    STARTED_EMPTY = enum.auto()


class DataFileMissingError(Exception):
    """The data folder exists without data.json: a vanished file (§2.9).

    Not an OSError, which means a folder Rature cannot use (§3.6).
    """


class DataFileUnreadableError(Exception):
    """data.json exists but does not load: it may still be arriving (§3.6)."""


class EnsureOutcome(enum.Enum):
    """What one App.ensure_day call did about persistence.

    IDLE: no rollover was due and no earlier save was still pending.
    SAVED: a write reached disk (a due rollover, or a retry of a pending
    one). SAVE_FAILED: a write was attempted and raised OSError; the
    rolled-over state is still only in memory and stays pending.
    """

    IDLE = enum.auto()
    SAVED = enum.auto()
    SAVE_FAILED = enum.auto()


class EnsureResult(NamedTuple):
    """What App.ensure_day returns: the persistence outcome and, when a
    rollover ran, the day it archived (None otherwise)."""

    outcome: EnsureOutcome
    archived: Day | None


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
        # True between a change made outside any gesture (a rollover that
        # archived a day, a confirmed empty day) and the write that persists
        # it: a failed write leaves it set so ensure_day retries.
        self._save_pending = False
        # Identifiers of this device's deletions since launch, most recent
        # last (SPECIFICATION.md §3.2, ADR 0009). Here rather than in Session
        # because it outlives the data it points into.
        self._undo_stack: list[str] = []

    @property
    def save_pending(self) -> bool:
        """A rollover or a confirmed empty day is not yet written to disk."""
        return self._save_pending

    @property
    def can_undo(self) -> bool:
        """A deletion made on this device today can still be undone."""
        return bool(self._undo_stack)

    @classmethod
    def open(
        cls,
        data_dir: Path | None = None,
        *,
        clock: Callable[[], datetime] = _default_clock,
    ) -> App:
        """Load the data file, then catch up on any due rollover.

        Returns an App whose day already matches the current reference
        date (SPECIFICATION.md §2.5): the caller never has to know a
        rollover happened, let alone run it itself. Creates nothing and
        never replaces a file (§2.9): a first launch starts on an empty day
        in memory, born on disk with the first gesture. Raises
        DataFileMissingError or DataFileUnreadableError for start_empty to
        settle once the user has decided, FutureVersionError for a newer
        file, and OSError for a folder or file it cannot reach (§3.6).
        """
        resolved_dir = data_dir if data_dir is not None else storage.xdg_data_dir()
        _logger.info("starting, data directory: %s", resolved_dir)
        storage.remove_stale_temp_files(data_dir=resolved_dir)
        if storage.data_dir_exists(data_dir=resolved_dir):
            app = cls._load(resolved_dir, clock)
        else:
            app = cls._empty(resolved_dir, clock, StartupOutcome.FIRST_LAUNCH)
        app.ensure_day()
        return app

    @classmethod
    def start_empty(
        cls,
        data_dir: Path,
        *,
        clock: Callable[[], datetime] = _default_clock,
    ) -> App:
        """The user's confirmed way out of a missing or unreadable file (§3.6).

        Reads again first: a file delivered while the confirmation was open
        is loaded, never replaced. Otherwise an unreadable file is set aside
        and the empty day is written at once: the confirmation is the
        gesture. A failed write of that day keeps it pending, for the banner
        of §3.6 situation 3. A failed set-aside raises OSError, situation 4.
        """
        try:
            return cls.open(data_dir, clock=clock)
        except DataFileMissingError:
            pass
        except DataFileUnreadableError:
            aside = storage.set_aside(clock(), data_dir=data_dir)
            _logger.warning("set an unreadable data file aside: %s", aside)
        app = cls._empty(data_dir, clock, StartupOutcome.STARTED_EMPTY)
        app._save_pending = True
        app.ensure_day()
        return app

    @classmethod
    def _load(cls, data_dir: Path, clock: Callable[[], datetime]) -> App:
        path = storage.main_file_path(data_dir=data_dir)
        try:
            store = storage.load(data_dir=data_dir)
        except FileNotFoundError as error:
            _logger.warning("the data file is missing: %s", path)
            raise DataFileMissingError(path) from error
        except (ValueError, KeyError, TypeError) as error:
            _logger.warning("the data file cannot be read: %s", path)
            raise DataFileUnreadableError(path) from error
        try:
            storage.restrict_data_dir_permissions(data_dir=data_dir)
        except OSError:
            # Self-healing, not a startup requirement (ADR 0003 addendum):
            # the folder exists, since the file was just read from it, and a
            # permission narrowing is nice, not essential, to have.
            _logger.warning(
                "could not restrict data directory permissions: %s", data_dir
            )
        return cls(
            data_dir=data_dir,
            session=store.into_session(),
            clock=clock,
            startup=StartupOutcome.LOADED,
        )

    @classmethod
    def _empty(
        cls,
        data_dir: Path,
        clock: Callable[[], datetime],
        startup: StartupOutcome,
    ) -> App:
        return cls(
            data_dir=data_dir,
            session=Session(Day(date=reference_date(clock()))),
            clock=clock,
            startup=startup,
        )

    def ensure_day(self) -> EnsureResult:
        """Run the SPECIFICATION.md §2.5 rollover if due, and persist it.

        roll_over, archive, then save, in that order. A save that raises
        OSError is reported as EnsureResult(SAVE_FAILED, old_day), not
        propagated: the rollover already happened in memory and was
        archived, so a later call retries the write while _save_pending is
        set, without a second roll_over or a second archive. Returns
        IDLE when nothing was due and nothing was pending.
        """
        now = self.clock()
        archived: Day | None = None
        if self.session.rollover_due(now):
            archived = self.session.roll_over(now)
            # The journal left with the day, and archiving below may raise.
            self._undo_stack.clear()
            _logger.info(
                "day rolled over from %s to %s", archived.date, self.session.day.date
            )
            storage.archive(archived, data_dir=self.data_dir)
            self._save_pending = True
        if not self._save_pending:
            return EnsureResult(EnsureOutcome.IDLE, archived)
        try:
            self._save()
        except OSError:
            return EnsureResult(EnsureOutcome.SAVE_FAILED, archived)
        return EnsureResult(EnsureOutcome.SAVED, archived)

    def archives(self) -> list[date]:
        """Dates with an archived day, most recent first."""
        return storage.list_archives(data_dir=self.data_dir)

    def search_archives(self, query: str) -> list[date]:
        """SPECIFICATION.md §3.13: archived dates holding a task that matches query.

        Same order as archives(), most recent first. A query that is empty
        or only whitespace returns archives() unchanged. An archive that
        fails to read is skipped, never raised: one unreadable file does
        not sink the whole search (§3.5, §3.13). Matching is the case- and
        accent-insensitive substring test of search.day_matches.
        """
        if not query.strip():
            return self.archives()
        matches: list[date] = []
        for day_date in self.archives():
            try:
                day = self.read_archive(day_date)
            except (OSError, ValueError, KeyError, TypeError, FutureVersionError):
                continue
            if search.day_matches(day, query):
                matches.append(day_date)
        return matches

    def read_archive(self, day_date: date) -> Day:
        """Load one archived day. See storage.load_archive for what can raise."""
        return storage.load_archive(day_date, data_dir=self.data_dir)

    def archive_matches(self, day: Day, query: str) -> bool:
        """SPECIFICATION.md §3.13's match test against an already-loaded day.

        The Archives window reads each archive once (read_archive) and
        keeps the Day for its lifetime, then filters with this instead of
        search_archives, which would reread every file per keystroke.
        ui/ goes through App and never imports rature.core.search.
        """
        return search.day_matches(day, query)

    def statistics(self) -> list[tuple[date, stats.DayCounts]]:
        """SPECIFICATION.md §3.14: (date, counts) per archived day.

        Most recent first, exactly archives()' order. An archive that fails
        to read is skipped, never raised, like search_archives (§3.13).
        Per-period totals are summed in the interface, not here.
        """
        rows: list[tuple[date, stats.DayCounts]] = []
        for day_date in self.archives():
            try:
                day = self.read_archive(day_date)
            except (OSError, ValueError, KeyError, TypeError, FutureVersionError):
                continue
            rows.append((day_date, stats.day_counts(day)))
        return rows

    def archived_session(self, day_date: date) -> Session:
        """A read-only Session wrapping one archived day.

        SPECIFICATION.md §3.2: block order (struck above active) is
        Session.view()'s, never recomputed in the interface. This gives the
        Archives window (§3.5) the same struck/active split the Day view
        reads from the live session. Raises whatever read_archive raises.
        """
        return Session(self.read_archive(day_date))

    def archive_session_from(self, day: Day) -> Session:
        """A read-only Session around an already-loaded archived Day.

        Same result as archived_session(day_date), for a caller that holds
        the Day itself: the Archives window caches parsed archives and
        should not reread the file to render one. Keeps Session out of ui/
        (ARCHITECTURE.md: only App bridges ui/ to core/).
        """
        return Session(day)

    def day_text(self) -> str:
        """SPECIFICATION.md §3.12: the current day as plain text."""
        return export.day_text(self.session)

    def archived_day_text(self, day_date: date) -> str:
        """SPECIFICATION.md §3.12: an archived day as plain text.

        Raises whatever archived_session raises for a missing or unreadable
        archive.
        """
        return export.day_text(self.archived_session(day_date))

    def _save(self) -> None:
        storage.save(Store.from_session(self.session), data_dir=self.data_dir)
        # A write that returned means whatever was pending is now on disk.
        # Only ensure_day sets the flag, so a mutation's save clearing it
        # is a harmless no-op in the common case.
        self._save_pending = False

    # Mutations below wrap the matching Session method: supply now/today
    # from self.clock() where the operation needs one, then save. Business
    # errors (LockedError, KeyError, ValueError) come straight from Session
    # and are not caught here.

    def add(self, text: str) -> Task:
        task = self.session.add(text)
        self._save()
        return task

    def add_struck(self, text: str) -> Task:
        task = self.session.add_struck(text, now=self.clock())
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

    def set_priority(self, task_id: str, *, priority: bool) -> None:
        self.session.set_priority(task_id, priority=priority)
        self._save()

    def delete(self, task_id: str) -> None:
        self.session.delete(task_id, now=self.clock())
        # Before the write: a failed write leaves the deletion in memory
        # (see the class docstring), and it stays undoable.
        self._undo_stack.append(task_id)
        self._save()

    def move_before(self, task_id: str, target_id: str | None) -> None:
        self.session.move_before(task_id, target_id)
        self._save()

    def undo_last_deletion(self) -> Task:
        """Undo this device's most recent deletion still on the stack."""
        if not self._undo_stack:
            raise ValueError("no deletion to undo")
        task = self.session.undo_deletion(self._undo_stack[-1])
        # Before the write: a failed write leaves the task restored in memory
        # (see the class docstring), and undoing it again would raise.
        self._undo_stack.pop()
        self._save()
        return task

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

    def set_reserve_priority(self, item_id: str, *, priority: bool) -> None:
        self.session.set_reserve_priority(item_id, priority=priority)
        self._save()

    def delete_from_reserve(self, item_id: str) -> None:
        self.session.delete_from_reserve(item_id)
        self._save()

    def move_reserve_before(self, item_id: str, target_id: str | None) -> None:
        self.session.move_reserve_before(item_id, target_id)
        self._save()

    def draw_from_reserve(self, item_id: str) -> Task:
        task = self.session.draw_from_reserve(item_id)
        self._save()
        return task

    def send_to_reserve(self, task_id: str) -> ReserveItem:
        item = self.session.send_to_reserve(task_id, today=reference_date(self.clock()))
        self._save()
        return item

    def add_to_tomorrow(self, text: str) -> PreparedTask:
        task = self.session.add_to_tomorrow(text)
        self._save()
        return task

    def rename_tomorrow(self, task_id: str, text: str) -> None:
        self.session.rename_tomorrow(task_id, text)
        self._save()

    def set_tomorrow_priority(self, task_id: str, *, priority: bool) -> None:
        self.session.set_tomorrow_priority(task_id, priority=priority)
        self._save()

    def delete_from_tomorrow(self, task_id: str) -> None:
        self.session.delete_from_tomorrow(task_id)
        self._save()

    def move_tomorrow_before(self, task_id: str, target_id: str | None) -> None:
        self.session.move_tomorrow_before(task_id, target_id)
        self._save()

    def move_to_tomorrow(self, task_id: str) -> PreparedTask:
        task = self.session.move_to_tomorrow(task_id)
        self._save()
        return task

    def move_reserve_to_tomorrow(self, item_id: str) -> PreparedTask:
        task = self.session.move_reserve_to_tomorrow(item_id)
        self._save()
        return task

    def move_to_today(self, task_id: str) -> Task:
        task = self.session.move_to_today(task_id)
        self._save()
        return task

    def send_tomorrow_to_reserve(self, task_id: str) -> ReserveItem:
        item = self.session.send_tomorrow_to_reserve(
            task_id, today=reference_date(self.clock())
        )
        self._save()
        return item

    def add_recurring(
        self,
        text: str,
        weekdays: list[int],
        cadence: Cadence = Cadence.WEEKLY,
    ) -> RecurringItem:
        item = self.session.add_recurring(
            text, weekdays, cadence=cadence, today=reference_date(self.clock())
        )
        self._save()
        return item

    def edit_recurring(
        self,
        item_id: str,
        *,
        text: str | None = None,
        weekdays: list[int] | None = None,
        cadence: Cadence | None = None,
    ) -> RecurringItem:
        item = self.session.edit_recurring(
            item_id,
            text=text,
            weekdays=weekdays,
            cadence=cadence,
            today=reference_date(self.clock()),
        )
        self._save()
        return item

    def cadence(self, item: RecurringItem) -> Cadence:
        """``item``'s cadence seen from the reference date's week.

        Feeds the row subtitle and the form's preselection
        (SPECIFICATION.md §3.4): the interface computes no parity.
        """
        return recurrence.cadence_on(item, reference_date(self.clock()))

    def recurring_due_tomorrow(self) -> list[RecurringItem]:
        """Templates due the day after the reference date (§3.16)."""
        return self.session.recurring_due_tomorrow(reference_date(self.clock()))

    def delete_recurring(self, item_id: str) -> None:
        self.session.delete_recurring(item_id)
        self._save()
