# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""``rature.core`` must never reach for the GTK stack.

This guards the rule stated in ``CLAUDE.md`` section 4 and
``docs/adr/0002-separation-core-ui.md``: the business logic stays testable
without a display. The check is an AST scan, so it fires on a forbidden
import even inside a function body.
"""

import ast
from pathlib import Path

FORBIDDEN_ROOTS = {"gi", "gtk", "adw", "gdk"}

CORE_DIR = Path(__file__).parent.parent / "src" / "rature" / "core"


def _imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_core_dir_exists() -> None:
    assert CORE_DIR.is_dir()


def test_no_core_module_imports_the_gtk_stack() -> None:
    offenders: dict[str, set[str]] = {}
    for path in sorted(CORE_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        forbidden = _imported_roots(tree) & FORBIDDEN_ROOTS
        if forbidden:
            offenders[str(path.relative_to(CORE_DIR.parent.parent.parent))] = forbidden
    assert not offenders, f"GTK imports found in core/: {offenders}"
