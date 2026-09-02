# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Plain-text rendering of a day for the clipboard copy (SPECIFICATION.md §3.12)."""

from datetime import date, datetime, timedelta, timezone

from rature.core.export import day_text
from rature.core.session import Day, Session

STAMP = datetime(2026, 8, 31, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


def make_session() -> Session:
    return Session(Day(date=date(2026, 8, 31)))


def test_an_empty_day_is_the_date_alone() -> None:
    text = day_text(make_session())
    assert text == date(2026, 8, 31).strftime("%A %d %B")
    assert "\n" not in text


def test_the_body_follows_the_date_after_a_blank_line() -> None:
    session = make_session()
    session.add("only one")
    lines = day_text(session).split("\n")
    assert lines[0] == date(2026, 8, 31).strftime("%A %d %B")
    assert lines[1] == ""
    assert lines[2] == "[ ] 1  only one"


def test_struck_tasks_come_first_with_their_marker() -> None:
    session = make_session()
    session.add("a")
    b = session.add("b")
    session.add("c")
    session.strike(b.id, now=STAMP)
    body = day_text(session).split("\n\n", 1)[1]
    assert body == "[x] 2  b\n[ ] 1  a\n[ ] 3  c"


def test_a_deleted_task_never_appears() -> None:
    session = make_session()
    gone = session.add("secret")
    session.add("kept")
    session.delete(gone.id, now=STAMP)
    assert day_text(session).endswith("[ ] 2  kept")
    assert "secret" not in day_text(session)


def test_text_is_verbatim_and_there_is_no_trailing_newline() -> None:
    session = make_session()
    session.add("  spaced out  ")
    text = day_text(session)
    assert text.endswith("[ ] 1    spaced out  ")
    assert not text.endswith("\n")
