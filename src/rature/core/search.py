# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Text matching for the archive search, SPECIFICATION.md §3.13.

Case- and accent-insensitive substring matching over a day's task text.
No file access, no gi: pure functions the App layer drives over archives.
"""

from __future__ import annotations

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rature.core.session import Day


def fold(text: str) -> str:
    """Normalise text for a §3.13 comparison: drop accents, then casefold.

    NFKD decomposition splits an accented character into its base letter
    plus a combining mark; the marks (``unicodedata.combining`` is truthy)
    are dropped, then ``casefold`` makes the result case-insensitive. So
    ``fold("Réparer") == fold("reparer")``. This is looser than the
    day-rollover duplicate check of §2.5, which keeps accents on purpose.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_marks.casefold()


def day_matches(day: Day, query: str) -> bool:
    """True when any task text of ``day`` contains ``query``, §3.13 folding applied.

    Only ``day.tasks`` is looked at. A deleted task lives in
    ``day.deletions``, never here, so §2.2 and §2.6 hold by construction:
    the search can never surface it. The caller passes a non-empty,
    already-stripped query; an empty needle would match every non-empty
    day and is App.search_archives' job to rule out first.
    """
    needle = fold(query)
    return any(needle in fold(task.text) for task in day.tasks)
