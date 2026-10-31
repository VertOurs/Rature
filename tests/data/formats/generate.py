# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Regenerate the data files written by released versions of Rature.

Each tag's own rature.core runs the same scenario over a few days, so
the files below <tag>/ are exactly what that release wrote to disk:
data.json plus its archives. test_core_validation.py loads every one of
them with the current code, migration included.

Run from the repository root, only when adding a tag to TAGS:

    python3 tests/data/formats/generate.py

Not collected by pytest. Uses git and the tag's pure-Python core only;
no gi, no network.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# One tag per release a user may still have data from, covering every
# file version: 1 (1.0.0, 1.5.0), 2 (1.6.0), 3 (1.7.1), 4 (1.8.0, 2.1.1).
TAGS = ("v1.0.0", "v1.5.0", "v1.6.0", "v1.7.1", "v1.8.0", "v2.1.1")

HERE = Path(__file__).resolve().parent


def _scenario(tree: Path, out: Path) -> None:
    """Drive the tag's App through four days; runs inside the old tree."""
    sys.path.insert(0, str(tree / "src"))
    from datetime import datetime, timedelta, timezone

    from rature.core import app as app_module

    paris = timezone(timedelta(hours=2))
    # 2026-08-24 is a Monday.
    now = [datetime(2026, 8, 24, 9, 0, tzinfo=paris)]
    app = app_module.App.open(out, clock=lambda: now[0])

    def has(name: str) -> bool:
        return hasattr(app, name)

    # Weekly on Tuesdays, every other week on Wednesdays where supported:
    # the rollovers below bring recurring tasks into the days.
    app.add_recurring("water plants", [1])
    cadence = getattr(app_module, "Cadence", None)
    if cadence is not None:
        app.add_recurring("bins", [2], cadence.EVERY_OTHER_FROM_THIS_WEEK)

    # Four days, the same gestures each day: every archive and the final
    # data.json carry every kind of entry the release supports.
    for day in range(4):
        if day:
            now[0] += timedelta(days=1)
            app.ensure_day()
        first = app.add(f"écrire les tests ✓ {day}")
        second = app.add(f"call the bank {day}")
        third = app.add(f"never mind {day}")
        app.strike(first.id)
        app.delete(third.id)
        if has("add_struck"):
            app.add_struck(f"already done {day}")
        if has("set_priority"):
            app.set_priority(second.id, priority=True)
        bike = app.add_to_reserve(f"fix the bike {day}")
        app.add_to_reserve(f"read the manual {day}")
        app.draw_from_reserve(bike.id)
        if has("set_reserve_priority"):
            app.set_reserve_priority(app.session.reserve[0].id, priority=True)
        if has("add_to_tomorrow"):
            app.add_to_tomorrow(f"prepare the slides {day}")
            app.move_reserve_to_tomorrow(app.session.reserve[-1].id)
        for entry in app.session.day.tasks:
            if entry.template_id is not None and not entry.done:
                app.strike(entry.id)


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--scenario":
        _scenario(Path(sys.argv[2]), Path(sys.argv[3]))
        return
    repo = HERE.parents[2]
    for tag in TAGS:
        target = HERE / tag
        shutil.rmtree(target, ignore_errors=True)
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            tree.mkdir()
            archive = subprocess.run(
                ["git", "-C", str(repo), "archive", tag, "src/rature/core"],
                check=True,
                capture_output=True,
            ).stdout
            subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
            data = Path(tmp) / "data"
            subprocess.run(
                [sys.executable, "-I", __file__, "--scenario", str(tree), str(data)],
                check=True,
            )
            shutil.copytree(data, target)
        print(f"{tag}: {sorted(p.name for p in target.rglob('*.json'))}")


if __name__ == "__main__":
    main()
