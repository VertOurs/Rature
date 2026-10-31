# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Strict, field-by-field reading of the decoded data files.

json.loads accepts any shape. Without these checks a wrong type passes
from_dict and only breaks later, in the interface ("done": "yes" reads
as struck, "tasks": {} as an empty list that the next write makes
permanent). Every helper raises an error App.open and the archive
readers already catch: KeyError for a missing key, TypeError for a
wrong type, ValueError for an unexpected key.

Messages name the key and the types, never the value: a value can be
the text of a task.
"""

from __future__ import annotations

from typing import Any


def _type_name(value: object) -> str:
    return type(value).__name__


def exact_keys(data: dict[str, Any], expected: frozenset[str]) -> None:
    """Refuse a missing or an unexpected key.

    A field is only ever added through a migration, so a key this
    version does not know means a damaged file or another writer, and
    keeping it would mean dropping it silently at the next save.
    """
    missing = expected - data.keys()
    if missing:
        raise KeyError(f"missing keys: {', '.join(sorted(missing))}")
    unexpected = data.keys() - expected
    if unexpected:
        raise ValueError(f"unexpected keys: {', '.join(sorted(unexpected))}")


def mapping(value: object, where: str) -> dict[str, Any]:
    """A JSON object; where names the list or key it was found in."""
    if not isinstance(value, dict):
        raise TypeError(f"{where}: expected an object, got {_type_name(value)}")
    return value


def text(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise TypeError(f"{key}: expected str, got {_type_name(value)}")
    return value


def optional_text(data: dict[str, Any], key: str) -> str | None:
    value = data[key]
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{key}: expected str or null, got {_type_name(value)}")
    return value


def integer(data: dict[str, Any], key: str) -> int:
    value = data[key]
    # bool subclasses int: true would otherwise read as 1.
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key}: expected int, got {_type_name(value)}")
    return value


def flag(data: dict[str, Any], key: str) -> bool:
    value = data[key]
    if not isinstance(value, bool):
        raise TypeError(f"{key}: expected bool, got {_type_name(value)}")
    return value


def objects(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """A list whose every entry is a JSON object."""
    value = data[key]
    if not isinstance(value, list):
        raise TypeError(f"{key}: expected a list, got {_type_name(value)}")
    return [mapping(entry, key) for entry in value]


def integers(data: dict[str, Any], key: str) -> list[int]:
    value = data[key]
    if not isinstance(value, list):
        raise TypeError(f"{key}: expected a list, got {_type_name(value)}")
    for entry in value:
        if not isinstance(entry, int) or isinstance(entry, bool):
            raise TypeError(f"{key}: expected int entries, got {_type_name(entry)}")
    return list(value)
