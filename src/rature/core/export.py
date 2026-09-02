# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Plain-text rendering of a day, for SPECIFICATION.md §3.12's clipboard copy.

No file access, no gi: a pure function over a Session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rature.core.session import Session


def day_text(session: Session) -> str:
    """Render a day as the plain text SPECIFICATION.md §3.12 describes.

    The long-form date, a blank line, then one ``[x]``/``[ ]`` line per task
    in ``Session.view()`` order (struck first). Deleted tasks and the
    ``deletions`` journal never appear. An empty day is the date alone; no
    trailing newline.
    """
    date_line = session.day.date.strftime("%A %d %B")
    lines = [
        f"[{'x' if task.done else ' '}] {task.num}  {task.text}"
        for task in session.view()
    ]
    if not lines:
        return date_line
    return f"{date_line}\n\n" + "\n".join(lines)
