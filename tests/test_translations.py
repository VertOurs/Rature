# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The launcher's gettext wiring actually backs a module-level `_()`.

rature.in calls gettext.bindtextdomain and gettext.textdomain (not
locale's, not gettext.install), the pair CLAUDE.md §4 rule 2 requires
every module to rely on through `from gettext import gettext as _`.
This exercises that exact mechanism with a throwaway domain and a
compiled .mo, no GTK or Flatpak needed.
"""

import gettext
import os
import re
import subprocess
from gettext import gettext as _
from pathlib import Path

import pytest

DOMAIN = "rature-test-fixture"
PO_DIR = Path(__file__).parent.parent / "po"


def test_bindtextdomain_and_textdomain_back_a_module_level_gettext(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    po = tmp_path / "fixture.po"
    po.write_text('msgid "Hello"\nmsgstr "Bonjour"\n', encoding="utf-8")
    mo_dir = tmp_path / "fr" / "LC_MESSAGES"
    mo_dir.mkdir(parents=True)
    subprocess.run(["msgfmt", str(po), "-o", str(mo_dir / f"{DOMAIN}.mo")], check=True)

    monkeypatch.setenv("LANGUAGE", "fr")
    gettext.bindtextdomain(DOMAIN, str(tmp_path))
    gettext.textdomain(DOMAIN)
    try:
        assert _("Hello") == "Bonjour"
    finally:
        gettext.textdomain("messages")


_LINGUAS = (PO_DIR / "LINGUAS").read_text().split()


@pytest.mark.parametrize("lang", _LINGUAS)
def test_catalogue_is_valid_and_fully_translated(lang: str) -> None:
    """Chantier 4's end criterion: msgfmt flags no untranslated string.

    Also runs msgfmt --check, so a %s that drifted between an English
    string and its translation fails here rather than at runtime.
    """
    result = subprocess.run(
        [
            "msgfmt",
            "--check",
            "--statistics",
            "-o",
            os.devnull,
            str(PO_DIR / f"{lang}.po"),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "LC_ALL": "C"},
    )
    assert result.returncode == 0, result.stderr
    # With LC_ALL=C the tally is English; a complete catalogue prints only
    # "N translated messages." with no "untranslated" or "fuzzy" clause.
    assert re.fullmatch(r"\d+ translated messages?\.\s*", result.stderr), result.stderr
