# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The long-form date takes its format from the catalogue (SPECIFICATION.md §3.8)."""

from datetime import date

import pytest

from rature.core import dates
from rature.core.dates import long_date


def test_without_a_catalogue_the_format_is_weekday_day_month() -> None:
    assert long_date(date(2026, 10, 29)) == date(2026, 10, 29).strftime("%A %-d %B")


def test_a_translated_format_reorders_the_parts_and_adds_words(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The Spanish catalogue's format. The C locale keeps the names in
    # English, which is enough to see the catalogue's order and words.
    monkeypatch.setattr(dates, "_", lambda message: "%A, %-d de %B")
    assert long_date(date(2026, 10, 29)) == "Thursday, 29 de October"
    assert long_date(date(2026, 11, 5)) == "Thursday, 5 de November"


def test_a_single_digit_day_drops_its_leading_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The French catalogue's format: "jeudi 5 novembre", not "jeudi 05".
    monkeypatch.setattr(dates, "_", lambda message: "%A %-d %B")
    assert long_date(date(2026, 11, 5)) == "Thursday 5 November"
    assert long_date(date(2026, 10, 29)) == "Thursday 29 October"


def test_without_a_matching_time_locale_the_source_format_is_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A Spanish catalogue over English names would read "Thursday, 29 de
    # October": the launcher turns the catalogue format off instead.
    monkeypatch.setattr(dates, "_", lambda message: "%A, %-d de %B")
    monkeypatch.setattr(dates, "_use_catalogue", True)
    dates.use_catalogue_format(False)
    assert long_date(date(2026, 10, 29)) == date(2026, 10, 29).strftime("%A %-d %B")
    dates.use_catalogue_format(True)
    assert long_date(date(2026, 10, 29)) == "Thursday, 29 de October"
