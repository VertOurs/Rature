# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The AUR checksum filler (build-aux/aur/fill_checksum.py)."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parent.parent / "build-aux" / "aur" / "fill_checksum.py"
_spec = importlib.util.spec_from_file_location("fill_checksum", _SCRIPT)
fill_checksum = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fill_checksum)

CHECKSUM = "0123456789abcdef" * 4


def _template(name: str) -> str:
    return (_SCRIPT.parent / name).read_text(encoding="utf-8")


def _version() -> str:
    return fill_checksum.PKGVER["PKGBUILD"].search(_template("PKGBUILD")).group(2)


@pytest.mark.parametrize("name", ["PKGBUILD", ".SRCINFO"])
def test_templates_in_the_repo_carry_skip(name: str) -> None:
    assert "SKIP" in _template(name)
    assert CHECKSUM not in _template(name)


def test_pkgbuild_gets_the_checksum() -> None:
    filled = fill_checksum.fill("PKGBUILD", _template("PKGBUILD"), _version(), CHECKSUM)
    assert f"sha256sums=('{CHECKSUM}')" in filled
    assert "sha256sums=('SKIP')" not in filled


def test_srcinfo_gets_the_checksum() -> None:
    filled = fill_checksum.fill(".SRCINFO", _template(".SRCINFO"), _version(), CHECKSUM)
    assert f"\tsha256sums = {CHECKSUM}\n" in filled
    assert "sha256sums = SKIP" not in filled


@pytest.mark.parametrize("name", ["PKGBUILD", ".SRCINFO"])
def test_another_version_is_refused(name: str) -> None:
    with pytest.raises(fill_checksum.TemplateError, match="pkgver"):
        fill_checksum.fill(name, _template(name), "0.0.1", CHECKSUM)


def test_a_template_without_skip_is_refused() -> None:
    filled = fill_checksum.fill("PKGBUILD", _template("PKGBUILD"), _version(), CHECKSUM)
    with pytest.raises(fill_checksum.TemplateError, match="SKIP"):
        fill_checksum.fill("PKGBUILD", filled, _version(), CHECKSUM)


def test_a_template_without_pkgver_is_refused() -> None:
    with pytest.raises(fill_checksum.TemplateError, match="found 0"):
        fill_checksum.fill("PKGBUILD", "sha256sums=('SKIP')\n", "1.0.0", CHECKSUM)


def test_main_writes_both_files(tmp_path: Path) -> None:
    archive = tmp_path / "rature.tar.gz"
    archive.write_bytes(b"not really an archive")
    expected = hashlib.sha256(b"not really an archive").hexdigest()
    output = tmp_path / "out"

    assert fill_checksum.main(_version(), str(archive), str(output)) == 0

    assert f"sha256sums=('{expected}')" in (output / "PKGBUILD").read_text()
    assert f"sha256sums = {expected}" in (output / ".SRCINFO").read_text()


def test_main_fails_on_a_version_mismatch(tmp_path: Path) -> None:
    archive = tmp_path / "rature.tar.gz"
    archive.write_bytes(b"")

    assert fill_checksum.main("0.0.1", str(archive), str(tmp_path / "out")) == 1
