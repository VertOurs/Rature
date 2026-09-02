# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Locale-derived weekday helpers used by the Recurring view.

rature.ui.weekdays imports only datetime, so it is exercised here like
core code, without a display or GTK.
"""

import calendar

import pytest

from rature.ui import weekdays


def test_abbrev_covers_seven_distinct_days() -> None:
    names = [weekdays.abbrev(day) for day in range(7)]
    assert len(set(names)) == 7
    assert all(names)


def test_monday_is_index_zero() -> None:
    # calendar.day_name is Monday-first too, so it pins the mapping
    # without hard-coding a locale's spelling.
    assert [weekdays.full(day) for day in range(7)] == list(calendar.day_name)


def test_subtitle_is_week_ordered_and_order_independent() -> None:
    assert weekdays.subtitle([2, 0]) == weekdays.subtitle([0, 2])
    assert weekdays.subtitle([0, 6]) == f"{weekdays.abbrev(0)} {weekdays.abbrev(6)}"


def test_empty_subtitle() -> None:
    assert weekdays.subtitle([]) == ""


@pytest.mark.parametrize("out_of_range", [-1, 7, 100])
def test_abbrev_and_full_reject_out_of_range(out_of_range: int) -> None:
    with pytest.raises(ValueError, match="out of range"):
        weekdays.abbrev(out_of_range)
    with pytest.raises(ValueError, match="out of range"):
        weekdays.full(out_of_range)
