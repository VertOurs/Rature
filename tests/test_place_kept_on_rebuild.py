# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Rebuilding the Day or Reserve rows keeps the user's place in the list.

Sending a reserve item to the day from mid-list used to throw focus, and
the scroll position with it, back to the first row. list_helpers'
keeping_place() is the fix; this checks both views rebuild inside it.

No gi: ui/ is not otherwise testable (CLAUDE.md §6), so this walks the
source instead of instantiating the widgets.
"""

import ast
from pathlib import Path

REPO = Path(__file__).parent.parent

_FILES = [
    REPO / "src" / "rature" / "ui" / "day_view.py",
    REPO / "src" / "rature" / "ui" / "reserve_view.py",
]


def _refresh_rebuilds_inside_keeping_place(source: str) -> bool:
    """True if refresh() rebuilds under a `with ...keeping_place(...)` block."""
    tree = ast.parse(source)
    refresh = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "refresh"
    )
    for node in ast.walk(refresh):
        if not isinstance(node, ast.With):
            continue
        context = node.items[0].context_expr
        if (
            isinstance(context, ast.Call)
            and isinstance(context.func, ast.Attribute)
            and context.func.attr == "keeping_place"
        ):
            return True
    return False


def test_a_rebuild_keeps_the_place_in_the_list() -> None:
    for path in _FILES:
        source = path.read_text(encoding="utf-8")
        assert _refresh_rebuilds_inside_keeping_place(source), (
            f"{path.relative_to(REPO)}: refresh() does not rebuild its rows "
            "inside list_helpers.keeping_place()"
        )
