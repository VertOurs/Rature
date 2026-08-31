# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Pure data structures for a day, the reserve and the recurring templates."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import uuid4


class Origin(enum.StrEnum):
    """Where a task came from."""

    DAY = "day"
    RESERVE = "reserve"
    RECURRING = "recurring"


def _new_id() -> str:
    return str(uuid4())


@dataclass(kw_only=True)
class Task:
    """One entry in the day's numbered list."""

    num: int
    text: str
    origin: Origin
    id: str = field(default_factory=_new_id)
    done: bool = False
    done_at: datetime | None = None
    source_id: str | None = None
    source_created: date | None = None
    template_id: str | None = None

    def __post_init__(self) -> None:
        if self.done_at is not None and self.done_at.tzinfo is None:
            raise ValueError("done_at must carry a UTC offset")
        if self.done != (self.done_at is not None):
            raise ValueError("done and done_at must agree")
        if self.origin == Origin.RESERVE and (
            self.source_id is None or self.source_created is None
        ):
            raise ValueError(
                "a reserve-origin task needs both source_id and source_created"
            )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "num": self.num,
            "text": self.text,
            "done": self.done,
            "done_at": self.done_at.isoformat() if self.done_at else None,
            "origin": self.origin.value,
            "source_id": self.source_id,
            "source_created": (
                self.source_created.isoformat() if self.source_created else None
            ),
            "template_id": self.template_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        done_at = data["done_at"]
        source_created = data["source_created"]
        return cls(
            id=data["id"],
            num=data["num"],
            text=data["text"],
            done=data["done"],
            done_at=datetime.fromisoformat(done_at) if done_at else None,
            origin=Origin(data["origin"]),
            source_id=data["source_id"],
            source_created=(
                date.fromisoformat(source_created) if source_created else None
            ),
            template_id=data["template_id"],
        )


@dataclass(kw_only=True)
class ReserveItem:
    """One entry in the reserve, the undated mother list."""

    text: str
    created: date
    id: str = field(default_factory=_new_id)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "created": self.created.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ReserveItem:
        return cls(
            id=data["id"],
            text=data["text"],
            created=date.fromisoformat(data["created"]),
        )


@dataclass(kw_only=True)
class RecurringItem:
    """A task template injected on its weekdays."""

    text: str
    weekdays: list[int]
    id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        # SPECIFICATION.md §2.7.2: weekdays is never empty; core refuses it.
        if not self.weekdays:
            raise ValueError("weekdays must not be empty")
        if any(day not in range(7) for day in self.weekdays):
            raise ValueError("weekdays entries must be 0..6, Monday is 0")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "weekdays": list(self.weekdays),
        }

    @classmethod
    def from_dict(cls, data: dict) -> RecurringItem:
        return cls(
            id=data["id"],
            text=data["text"],
            weekdays=list(data["weekdays"]),
        )


@dataclass(kw_only=True)
class Deletion:
    """A journal entry for a deleted task. Never shown, see ADR 0005.

    Carries enough of the task's state (done, done_at, source_created,
    template_id, index) to restore it exactly, as milestone 4's undo
    will need to.
    """

    id: str
    num: int
    text: str
    origin: Origin
    deleted_at: datetime
    index: int
    source_id: str | None = None
    source_created: date | None = None
    template_id: str | None = None
    done: bool = False
    done_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.deleted_at.tzinfo is None:
            raise ValueError("deleted_at must carry a UTC offset")
        if self.done != (self.done_at is not None):
            raise ValueError("done and done_at must agree")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "num": self.num,
            "text": self.text,
            "origin": self.origin.value,
            "source_id": self.source_id,
            "source_created": (
                self.source_created.isoformat() if self.source_created else None
            ),
            "template_id": self.template_id,
            "done": self.done,
            "done_at": self.done_at.isoformat() if self.done_at else None,
            "index": self.index,
            "deleted_at": self.deleted_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Deletion:
        done_at = data["done_at"]
        source_created = data["source_created"]
        return cls(
            id=data["id"],
            num=data["num"],
            text=data["text"],
            origin=Origin(data["origin"]),
            source_id=data["source_id"],
            source_created=(
                date.fromisoformat(source_created) if source_created else None
            ),
            template_id=data["template_id"],
            done=data["done"],
            done_at=datetime.fromisoformat(done_at) if done_at else None,
            index=data["index"],
            deleted_at=datetime.fromisoformat(data["deleted_at"]),
        )
