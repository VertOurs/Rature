# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The Flatpak repo-lint filter (build-aux/flatpak/repo_lint.py)."""

import importlib.util
import json
from pathlib import Path

_SCRIPT = Path(__file__).parent.parent / "build-aux" / "flatpak" / "repo_lint.py"
_spec = importlib.util.spec_from_file_location("repo_lint", _SCRIPT)
repo_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(repo_lint)

EXCEPTIONS = json.loads(
    (_SCRIPT.parent / "repo-lint-exceptions.json").read_text(encoding="utf-8")
)


def test_no_errors_is_clean() -> None:
    assert repo_lint.unexpected_errors({"errors": []}, EXCEPTIONS) == []
    assert repo_lint.unexpected_errors({}, EXCEPTIONS) == []


def test_only_excepted_errors_is_clean() -> None:
    assert repo_lint.unexpected_errors({"errors": list(EXCEPTIONS)}, EXCEPTIONS) == []


def test_an_unlisted_error_is_reported_and_order_is_kept() -> None:
    excepted = "appstream-external-screenshot-url"
    report = {"errors": [excepted, "finish-args-broken", "no-exportable-icon"]}
    assert repo_lint.unexpected_errors(report, EXCEPTIONS) == [
        "finish-args-broken",
        "no-exportable-icon",
    ]
