#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Fill the AUR files with the checksum of a release's source archive.

The archive GitHub serves for a tag contains PKGBUILD and .SRCINFO, so the
copies in the repository cannot hold its checksum: they carry SKIP. After
a tag, release.yml downloads the archive and runs this script, which
writes completed copies to attach to the release. No follow-up commit.

Usage: fill_checksum.py VERSION ARCHIVE OUTPUT_DIR
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

AUR_DIR = Path(__file__).parent

# Each pattern must match exactly once; group 1 is the line up to the value.
PKGVER = {
    "PKGBUILD": re.compile(r"(?m)^(pkgver=)(\S+)$"),
    ".SRCINFO": re.compile(r"(?m)^(\tpkgver = )(\S+)$"),
}
CHECKSUM = {
    "PKGBUILD": (re.compile(r"(?m)^(sha256sums=\(')SKIP('\))$"), r"\g<1>{}\g<2>"),
    ".SRCINFO": (re.compile(r"(?m)^(\tsha256sums = )SKIP$"), r"\g<1>{}"),
}


class TemplateError(ValueError):
    """A template does not have the shape this script expects."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fill(name: str, text: str, version: str, checksum: str) -> str:
    """The template `name` with its SKIP replaced by `checksum`.

    Refuses a template whose pkgver is not `version`: the checksum would
    then describe another release's archive.
    """
    versions = PKGVER[name].findall(text)
    if len(versions) != 1:
        raise TemplateError(f"{name}: expected one pkgver, found {len(versions)}")
    if versions[0][1] != version:
        raise TemplateError(f"{name}: pkgver is {versions[0][1]}, not {version}")
    pattern, replacement = CHECKSUM[name]
    filled, count = pattern.subn(replacement.format(checksum), text)
    if count != 1:
        raise TemplateError(f"{name}: expected one SKIP checksum, found {count}")
    return filled


def main(version: str, archive: str, output_dir: str) -> int:
    checksum = sha256_of(Path(archive))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    try:
        for name in CHECKSUM:
            text = (AUR_DIR / name).read_text(encoding="utf-8")
            filled = fill(name, text, version, checksum)
            (output / name).write_text(filled, encoding="utf-8")
    except TemplateError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    sys.stdout.write(f"sha256 {checksum}\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.stderr.write(__doc__.rsplit("\n\n", 1)[-1] + "\n")
        sys.exit(2)
    sys.exit(main(*sys.argv[1:]))
