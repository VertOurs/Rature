# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Guards on the packaging wiring: gettext lists, gresource, desktop entry.

These stay free of ``gi`` so they run on the tooling interpreter, which has
no PyGObject. The GTK window itself is only checked by launching the app,
see ``docs/internal/CHANTIER-0.md`` step 0.6.
"""

import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
DATA = REPO / "data"
APP_ID = "io.github.vertours.Rature"


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def test_linguas_lists_french() -> None:
    assert "fr" in (REPO / "po" / "LINGUAS").read_text(encoding="utf-8").split()


def test_every_potfiles_entry_exists() -> None:
    entries = [
        line.strip()
        for line in _read_lines(REPO / "po" / "POTFILES.in")
        if line.strip() and not line.startswith("#")
    ]
    missing = [entry for entry in entries if not (REPO / entry).is_file()]
    assert not missing, f"POTFILES.in points at missing files: {missing}"


def test_gresource_references_existing_files() -> None:
    tree = ET.parse(DATA / "rature.gresource.xml")
    files = [node.text for node in tree.iter("file")]
    assert files, "the gresource bundle is empty"
    missing = [name for name in files if not (DATA / name).is_file()]
    assert not missing, f"gresource references missing files: {missing}"


def test_desktop_entry_points_at_the_launcher_and_icon() -> None:
    text = (DATA / f"{APP_ID}.desktop.in").read_text(encoding="utf-8")
    assert "Exec=rature\n" in text
    assert f"Icon={APP_ID}\n" in text


def test_scalable_icon_is_installed_under_the_app_id() -> None:
    icon = DATA / "icons/hicolor/scalable/apps" / f"{APP_ID}.svg"
    assert icon.is_file()


@pytest.mark.skipif(
    shutil.which("desktop-file-validate") is None,
    reason="desktop-file-validate is not installed",
)
def test_desktop_file_validates(tmp_path: Path) -> None:
    # The source carries a .desktop.in suffix; the validator insists on
    # .desktop, and its keys are plain (no translation merge needed to lint).
    candidate = tmp_path / f"{APP_ID}.desktop"
    candidate.write_text(
        (DATA / f"{APP_ID}.desktop.in").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    result = subprocess.run(
        ["desktop-file-validate", str(candidate)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(
    shutil.which("appstreamcli") is None,
    reason="appstreamcli is not installed",
)
def test_metainfo_has_no_validation_errors() -> None:
    result = subprocess.run(
        [
            "appstreamcli",
            "validate",
            "--no-net",
            "--explain",
            str(DATA / f"{APP_ID}.metainfo.xml.in"),
        ],
        capture_output=True,
        text=True,
    )
    errors = [
        line for line in result.stdout.splitlines() if line.lstrip().startswith("E:")
    ]
    assert not errors, "\n".join(errors)
