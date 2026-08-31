# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Process entry point.

The GTK stack is imported inside :func:`main` on purpose: importing this
module must stay possible without PyGObject, so the test suite can run on an
interpreter that has no ``gi``.
"""

import sys


def main() -> int:
    """Start the application and return its exit code."""
    from rature.ui.application import RatureApplication

    app = RatureApplication()
    return app.run(sys.argv)
