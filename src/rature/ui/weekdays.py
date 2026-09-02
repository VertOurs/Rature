# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Locale-derived weekday names for the Recurring view.

No catalogue strings: strftime over a reference week that starts on a
Monday, the same mechanism as the Day view's date title. Correct in
every locale, provided the process locale is set (see src/rature.in).
"""

from __future__ import annotations

from datetime import date, timedelta

# 1 January 2024 is a Monday, so day index 0..6 maps to Monday..Sunday.
_REFERENCE_MONDAY = date(2024, 1, 1)


def _check(weekday: int) -> int:
    # Without this, timedelta would happily wrap: abbrev(7) would return
    # Monday again rather than signal a caller that lost track of the range.
    if not 0 <= weekday <= 6:
        raise ValueError(f"weekday out of range 0..6: {weekday}")
    return weekday


def abbrev(weekday: int) -> str:
    """Abbreviated name for a weekday, Monday is 0 (e.g. ``Mon``, ``lun.``)."""
    return (_REFERENCE_MONDAY + timedelta(days=_check(weekday))).strftime("%a")


def full(weekday: int) -> str:
    """Full name for a weekday, Monday is 0 (e.g. ``Monday``, ``lundi``)."""
    return (_REFERENCE_MONDAY + timedelta(days=_check(weekday))).strftime("%A")


def subtitle(weekdays: list[int]) -> str:
    """The selected days, abbreviated, in week order, space-separated."""
    return " ".join(abbrev(day) for day in sorted(weekdays))
