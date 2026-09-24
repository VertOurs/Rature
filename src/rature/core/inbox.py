# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Reading and filing the drop-box files of SPECIFICATION.md §2.8.

No gi import, no GSettings and no portal: this module only ever sees a
Path already resolved by ui/ (ADR 0007). It does not touch the reserve or
data.json; App.import_inbox wires it into a claim-read-save-finalize
sequence, the crash-safety addendum to ADR 0007's original design.
"""

from __future__ import annotations

import re
from pathlib import Path

_INBOX_NAME = re.compile(r"^inbox-.+\.txt$")
_PENDING_NAME = re.compile(r"^inbox-.+\.txt\.pending$")
_PROCESSED_DIR = "processed"
_PENDING_SUFFIX = ".pending"

# ADR 0007 addendum: caps how much of a dropped file is ever read into
# memory before it is safely claimed.
MAX_INBOX_FILE_SIZE = 1_000_000


class InboxFileTooLargeError(Exception):
    """An inbox-*.txt file is over MAX_INBOX_FILE_SIZE; treated as unreadable."""


def list_inbox_files(folder: Path) -> list[Path]:
    """Files directly in folder matching the §2.8 inbox-*.txt name.

    Only the name is checked, never the content: a sync client's .tmp or
    .part file left mid-transfer never matches this pattern and is left
    untouched, per ADR 0007 point 2. A missing folder is not an error
    here, it yields no files; the caller decides what that means. A
    symlink is skipped even when its name matches and its target is a
    plain file: the portal only grants access to what it resolved at
    picker time, and a symlink placed inside that folder can point
    anywhere on disk, outside that grant (ADR 0007 addendum).
    """
    if not folder.is_dir():
        return []
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and not path.is_symlink() and _INBOX_NAME.match(path.name)
    )


def check_inbox_file(path: Path) -> None:
    """Raise if path cannot be safely claimed, without moving it.

    SPECIFICATION.md §2.8 requires an unreadable or oversized file to
    stay exactly where it is; by the time claim() could run, it would
    already sit in processed/, in the open contradiction of that rule.
    Call this before claim(), never after.

    Raises InboxFileTooLargeError over MAX_INBOX_FILE_SIZE, or
    UnicodeDecodeError straight from the read, whichever fails first.
    OSError (the file vanished, a permission changed) is left uncaught
    for the caller, same as everywhere else in this module. Reading the
    whole, size-capped file here and discarding it is simpler than an
    incremental decode; App.import_inbox re-reads it anyway once claim()
    has moved it somewhere it is safe to keep.
    """
    if path.stat().st_size > MAX_INBOX_FILE_SIZE:
        raise InboxFileTooLargeError(path)
    path.read_text(encoding="utf-8-sig")


def read_inbox_lines(path: Path) -> list[str]:
    """One inbox file's content as its non-empty, stripped task lines.

    utf-8-sig: a leading UTF-8 byte-order mark, which some phone note
    apps write, is stripped rather than kept as a stray character on the
    first line; a file with no BOM decodes exactly as plain UTF-8 would.
    Raises UnicodeDecodeError, uncaught, if the content is not valid
    UTF-8 either way: SPECIFICATION.md §2.8 treats that file as
    unreadable, left in place, the caller responsible for the banner. An
    empty file, or one holding only blank lines, reads as an empty list;
    that is not an error, §2.8 moves it straight to processed/.
    """
    text = path.read_text(encoding="utf-8-sig")
    return [line.strip() for line in text.splitlines() if line.strip()]


def processed_dir(folder: Path) -> Path:
    """Where imported inbox files are filed, §2.8: never deleted."""
    return folder / _PROCESSED_DIR


def _unique_destination(destination: Path) -> Path:
    """destination if free, else the same name with -2, -3, ... inserted
    before its final extension (same spirit as storage.quarantine(), never
    silently overwriting a file already claimed or already processed).
    """
    if not destination.exists():
        return destination
    stem, suffix = destination.stem, destination.suffix
    n = 2
    while True:
        candidate = destination.with_name(f"{stem}-{n}{suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def claim(path: Path, folder: Path) -> Path:
    """Move an inbox file into folder/processed/<name>.pending.

    Creates processed/ on first use. This is the crash-safety boundary:
    once claim() returns, the file is out of the watched folder (so a
    sync client never sees or re-syncs it) but not yet counted as
    imported (App.import_inbox still has to read, add to the reserve and
    save). The anti-collision suffix of _unique_destination applies here
    too, so a .pending left over from an earlier, interrupted run is
    never overwritten by a same-named file dropped since.
    """
    destination = processed_dir(folder)
    destination.mkdir(parents=True, exist_ok=True)
    target = _unique_destination(destination / (path.name + _PENDING_SUFFIX))
    path.rename(target)
    return target


def finalize(pending_path: Path) -> Path:
    """Rename a claimed file from <name>.txt.pending to <name>.txt.

    Called only once a claimed file's content is safely accounted for
    (App.import_inbox). Same anti-collision suffix as claim(): a
    finalize() racing a second claim() of a same-named file never
    overwrites the earlier one's result.
    """
    final_name = pending_path.name.removesuffix(_PENDING_SUFFIX)
    target = _unique_destination(pending_path.with_name(final_name))
    pending_path.rename(target)
    return target


def list_pending_files(folder: Path) -> list[Path]:
    """processed/inbox-*.txt.pending left over from an interrupted import.

    App.import_inbox retries these before scanning the watched folder
    again: claim() already moved them out of it, so nothing there still
    points at them. A missing processed/ directory is not an error, it
    yields no files, same convention as list_inbox_files.
    """
    destination = processed_dir(folder)
    if not destination.is_dir():
        return []
    return sorted(
        path
        for path in destination.iterdir()
        if path.is_file() and _PENDING_NAME.match(path.name)
    )
