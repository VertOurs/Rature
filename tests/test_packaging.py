# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Packaging wiring guards; merged-file validation runs in the meson CI job."""

import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).parent.parent
DATA = REPO / "data"
APP_ID = "io.github.vertours.Rature"
MANIFEST = REPO / "build-aux" / "flatpak" / f"{APP_ID}.yml"


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


def test_manifest_keeps_the_locale_catalogue_in_the_app() -> None:
    # A split .Locale extension is not pulled by a --user install nor
    # bundled into the standalone .flatpak, which left the interface
    # untranslated. Keep the catalogue inside the app.
    lines = [line.strip() for line in _read_lines(MANIFEST)]
    assert "separate-locales: false" in lines
