# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""XDG paths, atomic writes and day archiving. Holds no business logic."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from rature.core import validation as check
from rature.core.migrations import CURRENT_VERSION, migrate
from rature.core.models import PreparedTask, RecurringItem, ReserveItem
from rature.core.session import DAY_KEYS, Day, Session

FILE_VERSION = CURRENT_VERSION
_MAIN_FILE = "data.json"
_ARCHIVE_DIR = "archive"
_ARCHIVE_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
# The temporary names of _atomic_write_json and _back_up_before_migration,
# and nothing else: a sync tool writes its own temporary files in this same
# folder (.syncthing.data.json.tmp), and removing one would break a delivery.
_MAIN_TEMP_NAME = re.compile(r"\.data\.json(\.v\d+\.bak)?\.\d+\.tmp")
_ARCHIVE_TEMP_NAME = re.compile(r"\.\d{4}-\d{2}-\d{2}\.json\.\d+\.tmp")
_logger = logging.getLogger(__name__)

# The whole key set of each file, after migration (validation.exact_keys).
_ARCHIVE_KEYS = DAY_KEYS | {"version"}
_MAIN_KEYS = _ARCHIVE_KEYS | {"reserve", "tomorrow", "recurring"}


def _day_part(data: dict[str, Any]) -> dict[str, Any]:
    return {key: data[key] for key in DAY_KEYS}


def xdg_data_dir() -> Path:
    root = os.environ.get("XDG_DATA_HOME")
    base = Path(root) if root else Path.home() / ".local" / "share"
    return base / "rature"


@dataclass(kw_only=True)
class Store:
    """The whole data file: the current day, the reserve, Tomorrow, templates."""

    day: Day
    reserve: list[ReserveItem] = field(default_factory=list)
    tomorrow: list[PreparedTask] = field(default_factory=list)
    recurring: list[RecurringItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": FILE_VERSION,
            **self.day.to_dict(),
            "reserve": [item.to_dict() for item in self.reserve],
            "tomorrow": [task.to_dict() for task in self.tomorrow],
            "recurring": [item.to_dict() for item in self.recurring],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Store:
        # Every key is required: since version 4 each one is always
        # written, so a missing "reserve" is a damaged file, not an empty
        # reserve to save over the real one.
        check.exact_keys(data, _MAIN_KEYS)
        return cls(
            day=Day.from_dict(_day_part(data)),
            reserve=[
                ReserveItem.from_dict(item) for item in check.objects(data, "reserve")
            ],
            tomorrow=[
                PreparedTask.from_dict(task) for task in check.objects(data, "tomorrow")
            ],
            recurring=[
                RecurringItem.from_dict(item)
                for item in check.objects(data, "recurring")
            ],
        )

    @classmethod
    def from_session(cls, session: Session) -> Store:
        return cls(
            day=session.day,
            reserve=session.reserve,
            tomorrow=session.tomorrow,
            recurring=session.recurring,
        )

    def into_session(self) -> Session:
        return Session(
            self.day,
            reserve=self.reserve,
            tomorrow=self.tomorrow,
            recurring=self.recurring,
        )


def _open_private(path: str, flags: int) -> int:
    # ADR 0003 addendum: 0o600 has no group/other bit for the umask to
    # remove, so this is the actual mode on every platform, not just
    # ones with a permissive default umask.
    return os.open(path, flags, 0o600)


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    # docs/adr/0003-single-json-file.md: temp file in the same directory,
    # flush, fsync the file, replace, then fsync the directory.
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8", opener=_open_private) as handle:
            json.dump(obj, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except OSError:
        # Path only, never the content: obj carries task and reserve text.
        _logger.error("failed to write %s", path)
        raise
    finally:
        # A no-op after a successful replace; removes the orphan on failure.
        tmp.unlink(missing_ok=True)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def main_file_path(*, data_dir: Path | None = None) -> Path:
    """Where the main data file lives, resolved the same way load/save do."""
    return (data_dir or xdg_data_dir()) / _MAIN_FILE


def load(*, data_dir: Path | None = None) -> Store:
    path = main_file_path(data_dir=data_dir)
    original = path.read_bytes()
    raw = json.loads(original.decode("utf-8"))
    store = Store.from_dict(migrate(raw))
    # migrate has validated raw: a dict with an int version.
    if raw["version"] < CURRENT_VERSION:
        _back_up_before_migration(path, original, raw["version"])
    return store


def _back_up_before_migration(path: Path, original: bytes, version: int) -> None:
    """Copy the on-disk file to data.json.v<N>.bak, SPECIFICATION.md §2.7.10.

    os.link never overwrites: an existing backup, the true original, is
    kept, and an interrupted copy leaves no truncated backup behind.
    """
    backup = path.with_name(f"{path.name}.v{version}.bak")
    if backup.exists():
        return
    tmp = path.with_name(f".{backup.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "wb", opener=_open_private) as handle:
            handle.write(original)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(tmp, backup)
    except FileExistsError:
        return
    except OSError:
        _logger.error("failed to back up %s before migration", path)
        raise
    finally:
        tmp.unlink(missing_ok=True)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    _logger.info("backed up the data file before migration: %s", backup)


def save(store: Store, *, data_dir: Path | None = None) -> None:
    target = data_dir or xdg_data_dir()
    # Explicit 0o700, not the umask-masked default: same reasoning as
    # _open_private (ADR 0003 addendum).
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    _atomic_write_json(target / _MAIN_FILE, store.to_dict())


def data_dir_exists(*, data_dir: Path | None = None) -> bool:
    """Whether the data folder exists: its absence means a first launch.

    os.stat rather than Path.exists, which also answers False on a refused
    access: a folder Rature cannot reach is not a first launch, and any
    OSError but FileNotFoundError goes up to the caller (SPECIFICATION.md
    §2.9, §3.6).
    """
    try:
        os.stat(data_dir or xdg_data_dir())
    except FileNotFoundError:
        return False
    return True


def restrict_data_dir_permissions(*, data_dir: Path | None = None) -> None:
    """Narrow the data directory itself to owner-only access (0o700).

    Called once per App.open (ADR 0003 addendum), not on every write: a
    directory at 0o700 already denies access to everything inside it,
    whatever each individual file's own mode is, so this alone also
    covers a data directory or archives created before this restriction
    existed, self-healing on every launch rather than only a fresh
    install. Raises OSError uncaught; the caller decides whether that is
    fatal.
    """
    target = data_dir or xdg_data_dir()
    os.chmod(target, 0o700)


def remove_stale_temp_files(*, data_dir: Path | None = None) -> None:
    """Remove Rature's own temporary files left behind by a crash (ADR 0009).

    Exact names only, in the data folder and in archive/. Symbolic links are
    ignored. A missing folder is nothing to do. Never raises: this is
    housekeeping, and a folder that is really unusable fails on the read
    that follows, with the error that belongs to it.
    """
    target = data_dir or xdg_data_dir()
    _remove_matching(target, _MAIN_TEMP_NAME)
    _remove_matching(target / _ARCHIVE_DIR, _ARCHIVE_TEMP_NAME)


def _remove_matching(directory: Path, name: re.Pattern[str]) -> None:
    try:
        with os.scandir(directory) as entries:
            stale = [entry for entry in entries if name.fullmatch(entry.name)]
    except FileNotFoundError:
        return
    except OSError:
        _logger.warning("could not look for temporary files in %s", directory)
        return
    for entry in stale:
        try:
            if entry.is_file(follow_symlinks=False):
                os.unlink(entry.path)
                _logger.info("removed a stale temporary file: %s", entry.path)
        except OSError:
            _logger.warning("could not remove a temporary file: %s", entry.path)


def set_aside(now: datetime, *, data_dir: Path | None = None) -> Path:
    """Rename the main file to data.json.<stamp>.bak; return its new path.

    Only ever on the user's confirmation (SPECIFICATION.md §3.6). The stamp
    comes from the caller, not the system clock: storage never reads it. On
    a name collision (two within the same second), a numeric suffix is
    added rather than overwriting the earlier file.
    """
    target = data_dir or xdg_data_dir()
    path = target / _MAIN_FILE
    stamp = now.strftime("%Y%m%d-%H%M%S")
    dest = path.with_name(f"{path.name}.{stamp}.bak")
    suffix = 2
    while dest.exists():
        dest = path.with_name(f"{path.name}.{stamp}-{suffix}.bak")
        suffix += 1
    path.rename(dest)
    return dest


def archive(day: Day, *, data_dir: Path | None = None) -> Path:
    """Write the day to archive/<day.date>.json, overwriting any earlier archive."""
    directory = (data_dir or xdg_data_dir()) / _ARCHIVE_DIR
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / f"{day.date.isoformat()}.json"
    _atomic_write_json(path, {"version": FILE_VERSION, **day.to_dict()})
    _logger.info("archived %s", path)
    return path


def list_archives(*, data_dir: Path | None = None) -> list[date]:
    """Dates with an archive file, most recent first.

    Reads file names only, never a file's content, so a corrupted
    archive cannot make this fail. Only names matching AAAA-MM-JJ.json
    count: _atomic_write_json's .<name>.<pid>.tmp sibling can survive
    a crash mid-write, and archive/ is exactly where it would land. A
    name of that shape that is not a real date (2026-02-30.json) is
    skipped, not raised on.
    """
    directory = (data_dir or xdg_data_dir()) / _ARCHIVE_DIR
    if not directory.is_dir():
        return []
    dates: list[date] = []
    for path in directory.iterdir():
        if not _ARCHIVE_NAME.match(path.name):
            continue
        try:
            dates.append(date.fromisoformat(path.name.removesuffix(".json")))
        except ValueError:
            continue
    return sorted(dates, reverse=True)


def load_archive(day_date: date, *, data_dir: Path | None = None) -> Day:
    """Load, migrate and return the archived Day for day_date.

    Raises whatever the file's actual problem is, uncaught: OSError if
    it is missing or unreadable, ValueError/KeyError/TypeError for
    invalid JSON or a malformed Day, and migrations.FutureVersionError
    for a version this build does not support. FutureVersionError does
    not subclass ValueError on purpose (see migrations.py): a caller
    copying App.open's except (ValueError, KeyError, TypeError)
    verbatim would let it through uncaught.
    """
    directory = (data_dir or xdg_data_dir()) / _ARCHIVE_DIR
    path = directory / f"{day_date.isoformat()}.json"
    raw = migrate(json.loads(path.read_text(encoding="utf-8")))
    check.exact_keys(raw, _ARCHIVE_KEYS)
    return Day.from_dict(_day_part(raw))
