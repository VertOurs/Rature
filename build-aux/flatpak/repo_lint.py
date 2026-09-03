#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Run flatpak-builder-lint on the built repo, minus known Flathub-only rules.

ROADMAP §5.1 wants the linter clean. Its `repo` check reports two errors
that are pure Flathub-submission requirements (screenshots mirrored to
dl.flathub.org and into the ostree commit); Rature self-hosts and does not
target Flathub. flatpak-builder-lint has no local exception file, so those
rules are listed with their reason in repo-lint-exceptions.json and
filtered here. Any other error fails the build.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

EXCEPTIONS_FILE = Path(__file__).with_name("repo-lint-exceptions.json")


def unexpected_errors(report: dict, exceptions: dict[str, str]) -> list[str]:
    """The linter errors not covered by an exception, in report order."""
    return [rule for rule in report.get("errors", []) if rule not in exceptions]


def main(repo: str) -> int:
    exceptions = json.loads(EXCEPTIONS_FILE.read_text(encoding="utf-8"))
    result = subprocess.run(
        ["flatpak-builder-lint", "repo", repo],
        capture_output=True,
        text=True,
        check=False,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    try:
        report = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        print("flatpak-builder-lint did not return JSON", file=sys.stderr)
        return 1
    for rule in report.get("errors", []):
        if rule in exceptions:
            print(f"excepted (Flathub-only): {rule} — {exceptions[rule]}")
    remaining = unexpected_errors(report, exceptions)
    if remaining:
        print(f"unexpected lint errors: {', '.join(remaining)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
