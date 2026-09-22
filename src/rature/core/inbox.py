# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Reading and filing the drop-box files of SPECIFICATION.md §2.8.

No gi import, no GSettings and no portal: this module only ever sees a
Path already resolved by ui/ (ADR 0007). It does not touch the reserve or
data.json; App.import_inbox (chantier 7.1, next step) wires this into a
save-then-move sequence.
"""

from __future__ import annotations

import re
from pathlib import Path

_INBOX_NAME = re.compile(r"^inbox-.+\.txt$")
_PROCESSED_DIR = "processed"


def list_inbox_files(folder: Path) -> list[Path]:
    """Files directly in folder matching the §2.8 inbox-*.txt name.

    Only the name is checked, never the content: a sync client's .tmp or
    .part file left mid-transfer never matches this pattern and is left
    untouched, per ADR 0007 point 2. A missing folder is not an error
    here, it yields no files; the caller decides what that means.
    """
    if not folder.is_dir():
        return []
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and _INBOX_NAME.match(path.name)
    )


def read_inbox_lines(path: Path) -> list[str]:
    """One inbox file's content as its non-empty, stripped task lines.

    Raises UnicodeDecodeError, uncaught, if the content is not valid
    UTF-8: SPECIFICATION.md §2.8 treats that file as unreadable, left in
    place, the caller responsible for the banner. An empty file, or one
    holding only blank lines, reads as an empty list; that is not an
    error, §2.8 moves it straight to processed/.
    """
    text = path.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


def processed_dir(folder: Path) -> Path:
    """Where imported inbox files are filed, §2.8: never deleted."""
    return folder / _PROCESSED_DIR


def move_to_processed(path: Path, folder: Path) -> Path:
    """Move an already-handled inbox file into folder/processed.

    Creates processed/ on first use. Called only once a file's content is
    safely accounted for elsewhere, per the ordering ADR 0007 decides.
    """
    destination = processed_dir(folder)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / path.name
    path.rename(target)
    return target
