# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The package imports and exposes a version."""

import rature


def test_version_is_the_first_milestone() -> None:
    assert rature.__version__ == "0.1.0"


def test_core_and_ui_are_importable() -> None:
    import rature.core
    import rature.ui

    assert rature.core.__doc__
    assert rature.ui.__doc__
