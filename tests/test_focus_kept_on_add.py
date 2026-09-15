# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""SPECIFICATION.md's Day and Reserve "Ajouter" rule: after a successful add,
the entry keeps focus, so rapid-fire dictation stays possible.

No gi: ui/ is not otherwise testable (CLAUDE.md §6), so this walks the
source instead of instantiating the widgets.
"""

import ast
from pathlib import Path

REPO = Path(__file__).parent.parent

# Both call their mutation through self.run_action(...); the entry that
# must keep focus is the module's own template child, named "entry".
_FILES = [
    REPO / "src" / "rature" / "ui" / "day_view.py",
    REPO / "src" / "rature" / "ui" / "reserve_view.py",
]


def _grab_focus_follows_a_successful_run_action(source: str) -> bool:
    """True if some `if self.run_action(...):` body calls .grab_focus().

    The mutation call sits in the `if`'s test expression, so Python only
    reaches the body, and grab_focus() with it, once run_action (and the
    full-view refresh it triggers) has already returned. A grab_focus()
    call placed before run_action, or outside this guard, would not
    survive that refresh: exactly the class of regression this guards
    against.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (
            isinstance(test, ast.Call)
            and isinstance(test.func, ast.Attribute)
            and test.func.attr == "run_action"
        ):
            continue
        for stmt in node.body:
            for call in ast.walk(stmt):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "grab_focus"
                ):
                    return True
    return False


def test_an_add_keeps_focus_in_the_entry() -> None:
    for path in _FILES:
        source = path.read_text(encoding="utf-8")
        assert _grab_focus_follows_a_successful_run_action(source), (
            f"{path.relative_to(REPO)}: no grab_focus() call guarded by a "
            "successful run_action(...) (SPECIFICATION.md's focus rule)"
        )
