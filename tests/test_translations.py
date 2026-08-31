# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The launcher's gettext wiring actually backs a module-level `_()`.

rature.in calls gettext.bindtextdomain and gettext.textdomain (not
locale's, not gettext.install), the pair CLAUDE.md §4 rule 7 requires
every module to rely on through `from gettext import gettext as _`.
This exercises that exact mechanism with a throwaway domain and a
compiled .mo, no GTK or Flatpak needed.
"""

import gettext
import subprocess
from gettext import gettext as _
from pathlib import Path

import pytest

DOMAIN = "rature-test-fixture"


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
