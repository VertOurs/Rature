# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Coordinates a Session with storage behind a single injectable clock.

No gi import: this is what a graphical interface calls into, never the
other way around.
"""

from __future__ import annotations

import copy
import enum
import logging
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from rature.core import export, recurrence, search, stats, storage
from rature.core.migrations import FutureVersionError
from rature.core.models import PreparedTask, RecurringItem, ReserveItem, Task

# Cadence is part of this module's interface: ui/ may only import
# rature.core.app, and the recurring wrappers below take it as is.
from rature.core.recurrence import Cadence

# LockedError re-exported: ui/ may only import rature.core.app, and its
# mutation wrappers below raise it straight from Session.
from rature.core.session import Day, LockedError, Session, reference_date
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


class GestureRefusedError(Exception):
    """A gesture no longer applies to data that changed elsewhere (§2.9).

    Expected, not a bug: not a LockedError, KeyError or ValueError, which the
    interface treats as one (§3.6). Nothing was written.
    """


def _parse(content: bytes, data_dir: Path) -> Store:
    try:
        return storage.parse_main(content, data_dir=data_dir)
    except (ValueError, KeyError, TypeError) as error:
        path = storage.main_file_path(data_dir=data_dir)
        _logger.warning("the data file cannot be read: %s", path)
        raise DataFileUnreadableError(path) from error


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
        # Days rolled over in memory and not yet archived, oldest first: the
        # first gesture writes them (SPECIFICATION.md §2.5). More than one
        # when the application stays open several nights without a gesture.
        self._pending_archives: list[Day] = []
        # Dates archived since take_written_archives last ran.
        self._written_archives: list[date] = []
        # The main file as last read or written, None until there is one.
        self._fingerprint: str | None = None
        # A write failed and its change lives only in memory (§2.9).
        self._write_failed = False
        # Fresh data replaced memory since take_reloaded last ran.
        self._reloaded = False
        # Identifiers of this device's deletions since launch, most recent
        # last (SPECIFICATION.md §3.2, ADR 0009). Here rather than in Session
        # because it outlives the data it points into.
        self._undo_stack: list[str] = []

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
        gesture. A failed write of that day leaves write_failed set, for the
        banner of §3.6 situation 3. A failed set-aside raises OSError,
        situation 4.
        """
        try:
            return cls.open(data_dir, clock=clock)
        except DataFileMissingError:
            pass
        except DataFileUnreadableError:
            aside = storage.set_aside(clock(), data_dir=data_dir)
            _logger.warning("set an unreadable data file aside: %s", aside)
        app = cls._empty(data_dir, clock, StartupOutcome.STARTED_EMPTY)
        app._save_confirmed()
        return app

    def save_device_data(self) -> None:
        """The user's confirmed way out of a failed re-read while running (§3.6).

        Memory holds the last successful read, reserve and recurring tasks
        included, so that is what gets written, never an empty day. Reads
        again first: a file delivered while the confirmation was open is
        loaded, never replaced. Otherwise an unreadable file is set aside and
        memory is written at once. After a failed write, the next gesture
        writes without asking: the user has already chosen. A failed set-aside
        raises OSError, situation 4.
        """
        try:
            self.reread()
        except DataFileMissingError:
            pass
        except DataFileUnreadableError:
            aside = storage.set_aside(self.clock(), data_dir=self.data_dir)
            _logger.warning("set an unreadable data file aside: %s", aside)
        else:
            return
        self._fingerprint = None
        self._save_confirmed()

    def _save_confirmed(self) -> None:
        # The confirmation is the gesture. A failed write leaves write_failed
        # set, for the banner of §3.6 situation 3.
        try:
            self._save()
        except OSError:
            _logger.warning("could not write the data in %s", self.data_dir)

    @classmethod
    def _load(cls, data_dir: Path, clock: Callable[[], datetime]) -> App:
        path = storage.main_file_path(data_dir=data_dir)
        try:
            content = storage.read_main(data_dir=data_dir)
        except FileNotFoundError as error:
            _logger.warning("the data file is missing: %s", path)
            raise DataFileMissingError(path) from error
        store = _parse(content, data_dir)
        try:
            storage.restrict_data_dir_permissions(data_dir=data_dir)
        except OSError:
            # Self-healing, not a startup requirement (ADR 0003 addendum):
            # the folder exists, since the file was just read from it, and a
            # permission narrowing is nice, not essential, to have.
            _logger.warning(
                "could not restrict data directory permissions: %s", data_dir
            )
        app = cls(
            data_dir=data_dir,
            session=store.into_session(),
            clock=clock,
            startup=StartupOutcome.LOADED,
        )
        app._fingerprint = storage.fingerprint(content)
        return app

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

    def ensure_day(self) -> Day | None:
        """Run the SPECIFICATION.md §2.5 rollover in memory if due.

        Never writes: the first gesture does, through _save. Returns the day
        it rolled away from, or None when nothing was due. The undo stack
        empties here, since the journal leaves with the day.
        """
        now = self.clock()
        if not self.session.rollover_due(now):
            return None
        archived = self.session.roll_over(now)
        self._undo_stack.clear()
        self._pending_archives.append(archived)
        _logger.info(
            "day rolled over from %s to %s", archived.date, self.session.day.date
        )
        return archived

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

    def take_written_archives(self) -> list[date]:
        """Dates archived since the last call, for the windows that show them.

        Filled by the write of a gesture (§2.5), even if the main file then
        fails: the archive is on disk either way (§3.6 situation 3).
        """
        written, self._written_archives = self._written_archives, []
        return written

    def _save(self) -> None:
        # SPECIFICATION.md §2.5: the archives, oldest first, then the main
        # file. Each archive leaves the list once on disk, so a later retry
        # writes only what is still missing, and a failed archive stops
        # everything after it.
        self._write_failed = True
        while self._pending_archives:
            day = self._pending_archives[0]
            storage.archive(day, data_dir=self.data_dir)
            del self._pending_archives[0]
            self._written_archives.append(day.date)
        self._fingerprint = storage.save(
            Store.from_session(self.session), data_dir=self.data_dir
        )
        self._write_failed = False

    def reread(self) -> bool:
        """Read the main file again, and take what changed (§2.9).

        Writes nothing but the backup any load makes of an older format.

        Returns whether the file changed. An unchanged file leaves memory
        alone, a due rollover included: the gesture applies to the day on
        screen, and the timer rolls over within the minute. Raises what
        open() raises for a file that vanished or no longer loads.
        """
        try:
            content = storage.read_main(data_dir=self.data_dir)
        except FileNotFoundError as error:
            if self._fingerprint is None:
                return False  # not written yet: a first launch, or a failed write
            path = storage.main_file_path(data_dir=self.data_dir)
            _logger.warning("the data file is missing: %s", path)
            raise DataFileMissingError(path) from error
        digest = storage.fingerprint(content)
        if digest == self._fingerprint:
            return False
        store = _parse(content, self.data_dir)
        if self._write_failed:
            # SPECIFICATION.md §2.9, known limits.
            _logger.warning("fresh data replaced a change that could not be saved")
        self._write_failed = False
        self.session = store.into_session()
        self._fingerprint = digest
        self._pending_archives.clear()
        journal = {entry.id for entry in self.session.day.deletions}
        self._undo_stack = [item for item in self._undo_stack if item in journal]
        self._reloaded = True
        self.ensure_day()
        return True

    def catch_up(self) -> None:
        """Take what changed elsewhere and a due rollover, on return of focus.

        Writes nothing, like the timer (§3.1): an unchanged file with no
        rollover due leaves memory untouched, so nothing needs rebuilding.
        """
        self.reread()
        self.ensure_day()

    @property
    def write_failed(self) -> bool:
        """Whether a change lives only in memory after a failed write."""
        return self._write_failed

    def take_reloaded(self) -> bool:
        """Whether fresh data replaced memory since the last call."""
        reloaded, self._reloaded = self._reloaded, False
        return reloaded

    def _gesture[T](self, apply: Callable[[Session], T]) -> T:
        """One gesture (§2.9): read again, apply once, write.

        Refused on data that changed, the gesture raises GestureRefusedError
        and memory is exactly the data as read: nothing is written. On data
        that did not change, a refusal stays the bug it always was, and
        raises as is. A failed write leaves the change in memory, see the
        class docstring.
        """
        fresh = copy.deepcopy(self.session) if self.reread() else None
        try:
            result = apply(self.session)
        except (LockedError, KeyError, ValueError) as error:
            if fresh is None:
                raise
            self.session = fresh
            _logger.info("a gesture no longer applies to the fresh data")
            raise GestureRefusedError from error
        self._save()
        return result

    # Mutations below name the matching Session method for _gesture, and
    # supply now/today from self.clock() where the operation needs one.
    # Business errors (LockedError, KeyError, ValueError) come straight from
    # Session when the data did not change.

    def add(self, text: str) -> Task:
        return self._gesture(lambda session: session.add(text))

    def add_struck(self, text: str) -> Task:
        return self._gesture(lambda session: session.add_struck(text, now=self.clock()))

    def strike(self, task_id: str) -> None:
        self._gesture(lambda session: session.strike(task_id, now=self.clock()))

    def unstrike(self, task_id: str) -> None:
        self._gesture(lambda session: session.unstrike(task_id))

    def rename(self, task_id: str, text: str) -> None:
        self._gesture(lambda session: session.rename(task_id, text))

    def set_priority(self, task_id: str, *, priority: bool) -> None:
        self._gesture(lambda session: session.set_priority(task_id, priority=priority))

    def delete(self, task_id: str) -> None:
        def apply(session: Session) -> None:
            session.delete(task_id, now=self.clock())
            # Before the write: a failed write leaves the deletion in memory
            # (see the class docstring), and it stays undoable.
            self._undo_stack.append(task_id)

        self._gesture(apply)

    def move_before(self, task_id: str, target_id: str | None) -> None:
        self._gesture(lambda session: session.move_before(task_id, target_id))

    def undo_last_deletion(self) -> Task:
        """Undo this device's most recent deletion still on the stack.

        The target is chosen before reading again: gone from the fresh
        journal, the undo is refused rather than moved to an older deletion.
        """
        if not self._undo_stack:
            raise ValueError("no deletion to undo")
        target = self._undo_stack[-1]

        def apply(session: Session) -> Task:
            task = session.undo_deletion(target)
            # Before the write: a failed write leaves the task restored in
            # memory (see the class docstring), and undoing it again would
            # raise.
            self._undo_stack.pop()
            return task

        return self._gesture(apply)

    def lock(self) -> None:
        self._gesture(lambda session: session.lock())

    def unlock(self) -> None:
        self._gesture(lambda session: session.unlock())

    def add_to_reserve(self, text: str) -> ReserveItem:
        return self._gesture(
            lambda session: session.add_to_reserve(
                text, today=reference_date(self.clock())
            )
        )

    def rename_reserve(self, item_id: str, text: str) -> None:
        self._gesture(lambda session: session.rename_reserve(item_id, text))

    def set_reserve_priority(self, item_id: str, *, priority: bool) -> None:
        self._gesture(
            lambda session: session.set_reserve_priority(item_id, priority=priority)
        )

    def delete_from_reserve(self, item_id: str) -> None:
        self._gesture(lambda session: session.delete_from_reserve(item_id))

    def move_reserve_before(self, item_id: str, target_id: str | None) -> None:
        self._gesture(lambda session: session.move_reserve_before(item_id, target_id))

    def draw_from_reserve(self, item_id: str) -> Task:
        return self._gesture(lambda session: session.draw_from_reserve(item_id))

    def send_to_reserve(self, task_id: str) -> ReserveItem:
        return self._gesture(
            lambda session: session.send_to_reserve(
                task_id, today=reference_date(self.clock())
            )
        )

    def add_to_tomorrow(self, text: str) -> PreparedTask:
        return self._gesture(lambda session: session.add_to_tomorrow(text))

    def rename_tomorrow(self, task_id: str, text: str) -> None:
        self._gesture(lambda session: session.rename_tomorrow(task_id, text))

    def set_tomorrow_priority(self, task_id: str, *, priority: bool) -> None:
        self._gesture(
            lambda session: session.set_tomorrow_priority(task_id, priority=priority)
        )

    def delete_from_tomorrow(self, task_id: str) -> None:
        self._gesture(lambda session: session.delete_from_tomorrow(task_id))

    def move_tomorrow_before(self, task_id: str, target_id: str | None) -> None:
        self._gesture(lambda session: session.move_tomorrow_before(task_id, target_id))

    def move_to_tomorrow(self, task_id: str) -> PreparedTask:
        return self._gesture(lambda session: session.move_to_tomorrow(task_id))

    def move_reserve_to_tomorrow(self, item_id: str) -> PreparedTask:
        return self._gesture(lambda session: session.move_reserve_to_tomorrow(item_id))

    def move_to_today(self, task_id: str) -> Task:
        return self._gesture(lambda session: session.move_to_today(task_id))

    def send_tomorrow_to_reserve(self, task_id: str) -> ReserveItem:
        return self._gesture(
            lambda session: session.send_tomorrow_to_reserve(
                task_id, today=reference_date(self.clock())
            )
        )

    def add_recurring(
        self,
        text: str,
        weekdays: list[int],
        cadence: Cadence = Cadence.WEEKLY,
    ) -> RecurringItem:
        return self._gesture(
            lambda session: session.add_recurring(
                text, weekdays, cadence=cadence, today=reference_date(self.clock())
            )
        )

    def edit_recurring(
        self,
        item_id: str,
        *,
        text: str | None = None,
        weekdays: list[int] | None = None,
        cadence: Cadence | None = None,
    ) -> RecurringItem:
        return self._gesture(
            lambda session: session.edit_recurring(
                item_id,
                text=text,
                weekdays=weekdays,
                cadence=cadence,
                today=reference_date(self.clock()),
            )
        )

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
        self._gesture(lambda session: session.delete_recurring(item_id))
