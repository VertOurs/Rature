# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Per-day archive counters for the Statistics window, SPECIFICATION.md §3.14.

No file access, no gi: a pure function over an archived Day. Only numbers
leave here, never a task's text (§2.2, §2.6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rature.core.models import Origin

if TYPE_CHECKING:
    from rature.core.session import Day


@dataclass(frozen=True, kw_only=True)
class DayCounts:
    """The four numbers SPECIFICATION.md §3.14 shows for one archived day.

    Independent counts, not a partition: ``added`` is not the sum of the
    others, and ``to_reserve`` overlaps the unstruck tasks.
    """

    added: int
    struck: int
    deleted: int
    to_reserve: int


def day_counts(day: Day) -> DayCounts:
    """Count one archived day for SPECIFICATION.md §3.14.

    - ``added``: every task that received a number that day, the tasks still
      in the day plus the ``deletions`` journal's entries. Only the entry
      count is used, never the entries' text (§2.2, §2.6). Equals
      ``day.counter - 1``.
    - ``struck``: tasks marked done in the archived day. A struck-then-deleted
      task is gone from the day (§3.5) and counts only in ``deleted``.
    - ``deleted``: the number of ``deletions`` journal entries.
    - ``to_reserve``: unfinished, non-recurring tasks, what the rollover
      sends to the reserve (§2.5 points 2 and 3) before its de-duplication.
      The archive is written before that move, so this can exceed the number
      that actually landed in the reserve when two identical texts met.
    """
    return DayCounts(
        added=len(day.tasks) + len(day.deletions),
        struck=sum(1 for task in day.tasks if task.done),
        deleted=len(day.deletions),
        to_reserve=sum(
            1 for task in day.tasks if not task.done and task.origin != Origin.RECURRING
        ),
    )
