# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Which recurring templates apply on a given date.

The only place that knows the every-other-week parity rule,
SPECIFICATION.md §2.7.7.
"""

from __future__ import annotations

import enum
from datetime import date, timedelta

from rature.core.models import RecurringItem


class Cadence(enum.Enum):
    """How often a template applies, one value per state of the form.

    The every-other-week values are relative to a reference date: the
    week that holds it, or the one after. start_monday turns them into
    the stored Monday, cadence_on reads them back.
    """

    WEEKLY = "weekly"
    EVERY_OTHER_FROM_THIS_WEEK = "every-other-from-this-week"
    EVERY_OTHER_FROM_NEXT_WEEK = "every-other-from-next-week"


def monday_of(day: date) -> date:
    """The Monday that starts ``day``'s week."""
    return day - timedelta(days=day.weekday())


def _is_active_week(start: date, day: date) -> bool:
    # Weeks elapsed since the stored Monday, never the ISO week number:
    # ISO weeks 53 of 2026 and 1 of 2027 follow each other and are both
    # odd. Floor division keeps the parity right before start, too.
    return (monday_of(day) - start).days // 7 % 2 == 0


def is_due(item: RecurringItem, day: date) -> bool:
    """Whether ``item`` applies on ``day``: right weekday, active week."""
    if day.weekday() not in item.weekdays:
        return False
    start = item.every_other_week_from
    return start is None or _is_active_week(start, day)


def due_on(day: date, recurring: list[RecurringItem]) -> list[RecurringItem]:
    """The templates that apply on ``day``, in list order."""
    return [item for item in recurring if is_due(item, day)]


def cadence_on(item: RecurringItem, day: date) -> Cadence:
    """``item``'s cadence as seen from ``day``'s week, for the interface."""
    start = item.every_other_week_from
    if start is None:
        return Cadence.WEEKLY
    if _is_active_week(start, day):
        return Cadence.EVERY_OTHER_FROM_THIS_WEEK
    return Cadence.EVERY_OTHER_FROM_NEXT_WEEK


def start_monday(
    cadence: Cadence, today: date | None, current: date | None = None
) -> date | None:
    """The every_other_week_from value that ``cadence`` asks for.

    ``today`` is the reference date, required for both every-other-week
    values. ``current`` is the value already stored: when it makes the
    same weeks active, it is kept as is, so saving a form without
    touching its week never moves anything (SPECIFICATION.md §2.7.7).
    """
    if cadence is Cadence.WEEKLY:
        return None
    if today is None:
        raise ValueError("an every-other-week cadence needs today")
    monday = monday_of(today)
    if cadence is Cadence.EVERY_OTHER_FROM_NEXT_WEEK:
        monday += timedelta(weeks=1)
    if current is not None and _is_active_week(current, monday):
        return current
    return monday
