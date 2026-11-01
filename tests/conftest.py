# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Fixtures shared by every test module."""

from pathlib import Path

import pytest


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """A data folder that does not exist yet, as on a real first launch.

    Not tmp_path itself: a data folder that exists without data.json is a
    vanished file (SPECIFICATION.md §2.9), not a first launch.
    """
    return tmp_path / "rature"
