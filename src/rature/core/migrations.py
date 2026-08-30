# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The migration base. The format is born at version 1, so nothing to run yet."""

from __future__ import annotations

from collections.abc import Callable

CURRENT_VERSION = 1

# One entry per version step, keyed by the version it upgrades from. Each
# function returns the data with "version" bumped. Empty until a version 2.
_MIGRATIONS: dict[int, Callable[[dict], dict]] = {}


def _migration(from_version: int) -> Callable[[Callable[[dict], dict]], Callable]:
    def register(func: Callable[[dict], dict]) -> Callable[[dict], dict]:
        _MIGRATIONS[from_version] = func
        return func

    return register


def migrate(
    data: dict,
    *,
    target: int = CURRENT_VERSION,
    registry: dict[int, Callable[[dict], dict]] | None = None,
) -> dict:
    """Bring a raw data dict up to ``target``, or raise if it cannot."""
    steps = _MIGRATIONS if registry is None else registry
    version = data.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError(f"missing or invalid data version: {version!r}")
    if version > target:
        raise ValueError(f"data version {version} is newer than supported {target}")
    while version < target:
        step = steps.get(version)
        if step is None:
            raise ValueError(f"no migration from version {version}")
        data = step(data)
        version = data["version"]
    return data
