# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Text matching for the archive search (SPECIFICATION.md §3.13)."""

from datetime import date, datetime, timedelta, timezone

from rature.core.models import Deletion, Origin, Task
from rature.core.search import day_matches, fold
from rature.core.session import Day

PARIS = timezone(timedelta(hours=2))


def a_day(*texts: str) -> Day:
    return Day(
        date=date(2026, 8, 24),
        tasks=[
            Task(num=i + 1, text=text, origin=Origin.DAY)
            for i, text in enumerate(texts)
        ],
    )


def test_fold_drops_accents_and_lowercases() -> None:
    assert fold("Réparer le VÉLO") == fold("reparer le velo")


def test_fold_leaves_unaccented_text_only_lowercased() -> None:
    assert fold("Buy Bread") == "buy bread"


def test_day_matches_is_case_insensitive() -> None:
    assert day_matches(a_day("Call the dentist"), "DENTIST") is True


def test_day_matches_is_accent_insensitive() -> None:
    assert day_matches(a_day("réparer la chaîne"), "reparer") is True


def test_day_matches_is_a_substring_test() -> None:
    assert day_matches(a_day("reparer"), "parer") is True


def test_day_matches_checks_every_task_not_only_the_first() -> None:
    assert day_matches(a_day("buy bread", "answer Marie"), "marie") is True


def test_day_matches_is_false_when_no_task_contains_the_query() -> None:
    assert day_matches(a_day("buy bread", "call the dentist"), "zebra") is False


def test_day_matches_is_false_for_a_day_with_no_tasks() -> None:
    assert day_matches(a_day(), "anything") is False


def test_a_deleted_task_is_never_matched() -> None:
    day = a_day("kept")
    day.deletions.append(
        Deletion(
            id="gone",
            num=2,
            text="secret errand",
            origin=Origin.DAY,
            deleted_at=datetime(2026, 8, 24, 12, 0, tzinfo=PARIS),
            index=0,
        )
    )
    assert day_matches(day, "secret") is False
