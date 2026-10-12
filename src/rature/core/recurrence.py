# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Which recurring templates apply on a given date."""

from __future__ import annotations

from datetime import date

from rature.core.models import RecurringItem


def due_on(day: date, recurring: list[RecurringItem]) -> list[RecurringItem]:
    """The templates whose weekdays include ``day``'s weekday."""
    return [item for item in recurring if day.weekday() in item.weekdays]
