# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Import surface, and version agreement across the sources that pin it."""

import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import rature

REPO = Path(__file__).parent.parent


def _pyproject_version() -> str:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def _meson_version() -> str:
    text = (REPO / "meson.build").read_text(encoding="utf-8")
    match = re.search(r"\bversion:\s*'([^']*)'", text)
    assert match, "no version field in meson.build"
    return match.group(1)


def _metainfo_latest_release() -> str:
    tree = ET.parse(REPO / "data" / "io.github.vertours.Rature.metainfo.xml.in")
    release = tree.find("./releases/release")
    assert release is not None, "no <release> in the metainfo"
    version = release.get("version")
    assert version, "the latest <release> has no version attribute"
    return version


def test_version_sources_agree() -> None:
    sources = {
        "rature.__version__": rature.__version__,
        "pyproject.toml": _pyproject_version(),
        "meson.build": _meson_version(),
        "metainfo latest release": _metainfo_latest_release(),
    }
    assert len(set(sources.values())) == 1, sources


def test_core_and_ui_are_importable() -> None:
    import rature.core
    import rature.ui

    assert rature.core.__doc__
    assert rature.ui.__doc__
