# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Data format migrations, one function per version step."""

from __future__ import annotations

import logging
from collections.abc import Callable

CURRENT_VERSION = 4
_logger = logging.getLogger(__name__)


class FutureVersionError(Exception):
    """The data file was written by a newer version of Rature than this one.

    Deliberately not a ValueError subclass: a caller distinguishing this
    case from a genuinely corrupted file (see App.open) must not depend on
    the order of its except clauses to do it correctly.
    """


# One entry per version step, keyed by the version it upgrades from. Each
# function returns the data with "version" bumped.
_MIGRATIONS: dict[int, Callable[[dict], dict]] = {}


def _migration(from_version: int) -> Callable[[Callable[[dict], dict]], Callable]:
    def register(func: Callable[[dict], dict]) -> Callable[[dict], dict]:
        _MIGRATIONS[from_version] = func
        return func

    return register


@_migration(1)
def _every_other_week(data: dict) -> dict:
    """Version 2: every recurring template gains every_other_week_from.

    null means every week, what every version 1 template was. Archive
    files carry no "recurring" key; they only get the version bump. A
    template that is not an object raises TypeError, which App.open
    folds into the corrupted-file path. Builds a new dict, never edits
    the one it was given.
    """
    migrated = {**data, "version": 2}
    if "recurring" in data:
        migrated["recurring"] = [
            {**item, "every_other_week_from": None} for item in data["recurring"]
        ]
    return migrated


@_migration(2)
def _priority(data: dict) -> dict:
    """Version 3: tasks, deletion entries and reserve items gain priority.

    false for all of them, what every version 2 entry was. Archive files
    carry no "reserve" key; their tasks and deletions still get the
    field. Same guarantees as _every_other_week: a new dict, and an
    entry that is not an object raises TypeError.
    """
    migrated = {**data, "version": 3}
    for key in ("tasks", "deletions", "reserve"):
        if key in data:
            migrated[key] = [{**entry, "priority": False} for entry in data[key]]
    return migrated


@_migration(3)
def _tomorrow(data: dict) -> dict:
    """Version 4: the main file gains an empty "tomorrow" list.

    SPECIFICATION.md §2.5: the Tomorrow list lives in the main file only.
    Archive files carry no "reserve" key and get the version bump alone.
    A new dict, like the steps above.
    """
    migrated = {**data, "version": 4}
    if "reserve" in data:
        migrated["tomorrow"] = []
    return migrated


def migrate(
    data: dict,
    *,
    target: int = CURRENT_VERSION,
    registry: dict[int, Callable[[dict], dict]] | None = None,
) -> dict:
    """Bring a raw data dict up to ``target``, or raise if it cannot."""
    steps = _MIGRATIONS if registry is None else registry
    if not isinstance(data, dict):
        # A valid JSON file whose top level is a list, string or number:
        # data.get below would raise AttributeError, which neither App.open
        # nor the Archives window catches. Fold it into the corrupted-file
        # path they already handle.
        raise ValueError(f"data must be a JSON object, got {type(data).__name__}")
    version = data.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError(f"missing or invalid data version: {version!r}")
    if version > target:
        raise FutureVersionError(
            f"data version {version} is newer than supported {target}"
        )
    while version < target:
        step = steps.get(version)
        if step is None:
            raise ValueError(f"no migration from version {version}")
        data = step(data)
        new_version = data.get("version")
        if not isinstance(new_version, int) or new_version <= version:
            raise RuntimeError(f"migration from version {version} did not advance it")
        _logger.info("migrated data from version %d to %d", version, new_version)
        version = new_version
    return data
