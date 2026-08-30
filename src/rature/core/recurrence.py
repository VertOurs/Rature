# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Which recurring templates apply on a given weekday."""

from __future__ import annotations

from rature.core.models import RecurringItem


def due_on(weekday: int, recurring: list[RecurringItem]) -> list[RecurringItem]:
    """The templates whose weekdays include ``weekday``. Monday is 0."""
    if weekday not in range(7):
        raise ValueError("weekday must be 0..6, Monday is 0")
    return [item for item in recurring if weekday in item.weekdays]
