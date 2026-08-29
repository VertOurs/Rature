# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Process entry point."""

import sys


def main(version: str = "") -> int:
    """Start the application and return its exit code."""
    from rature.ui.application import RatureApplication

    app = RatureApplication(version)
    return app.run(sys.argv)
