# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""XDG paths, atomic writes and day archiving. Holds no business logic."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rature.core.migrations import CURRENT_VERSION, migrate
from rature.core.models import RecurringItem, ReserveItem
from rature.core.session import Day, Session

FILE_VERSION = CURRENT_VERSION
_MAIN_FILE = "data.json"
_ARCHIVE_DIR = "archive"


def xdg_data_dir() -> Path:
    root = os.environ.get("XDG_DATA_HOME")
    base = Path(root) if root else Path.home() / ".local" / "share"
    return base / "rature"


@dataclass(kw_only=True)
class Store:
    """The whole data file: the current day plus the reserve and templates."""

    day: Day
    reserve: list[ReserveItem] = field(default_factory=list)
    recurring: list[RecurringItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": FILE_VERSION,
            **self.day.to_dict(),
            "reserve": [item.to_dict() for item in self.reserve],
            "recurring": [item.to_dict() for item in self.recurring],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Store:
        return cls(
            day=Day.from_dict(data),
            reserve=[ReserveItem.from_dict(item) for item in data.get("reserve", [])],
            recurring=[
                RecurringItem.from_dict(item) for item in data.get("recurring", [])
            ],
        )

    @classmethod
    def from_session(cls, session: Session) -> Store:
        return cls(
            day=session.day,
            reserve=session.reserve,
            recurring=session.recurring,
        )

    def into_session(self) -> Session:
        return Session(self.day, reserve=self.reserve, recurring=self.recurring)


def _atomic_write_json(path: Path, obj: dict) -> None:
    # docs/adr/0003-fichier-json-unique.md: temp file in the same directory,
    # flush, fsync the file, replace, then fsync the directory.
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(obj, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        # A no-op after a successful replace; removes the orphan on failure.
        tmp.unlink(missing_ok=True)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def load(*, data_dir: Path | None = None) -> Store:
    path = (data_dir or xdg_data_dir()) / _MAIN_FILE
    raw = migrate(json.loads(path.read_text(encoding="utf-8")))
    return Store.from_dict(raw)


def save(store: Store, *, data_dir: Path | None = None) -> None:
    target = data_dir or xdg_data_dir()
    target.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(target / _MAIN_FILE, store.to_dict())


def quarantine(now: datetime, *, data_dir: Path | None = None) -> Path:
    """Rename the unreadable main file aside; return its new path.

    The stamp comes from the caller, not the system clock: storage never
    reads it. On a name collision (two quarantines within the same
    second), a numeric suffix is appended rather than overwriting the
    earlier one.
    """
    target = data_dir or xdg_data_dir()
    path = target / _MAIN_FILE
    stamp = now.strftime("%Y%m%d-%H%M%S")
    dest = path.with_name(f"{path.name}.bad-{stamp}")
    suffix = 2
    while dest.exists():
        dest = path.with_name(f"{path.name}.bad-{stamp}-{suffix}")
        suffix += 1
    path.rename(dest)
    return dest


def archive(day: Day, *, data_dir: Path | None = None) -> Path:
    """Write the day to archive/<day.date>.json, overwriting any earlier archive."""
    directory = (data_dir or xdg_data_dir()) / _ARCHIVE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{day.date.isoformat()}.json"
    _atomic_write_json(path, {"version": FILE_VERSION, **day.to_dict()})
    return path
