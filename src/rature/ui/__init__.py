# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""GTK layer for Rature.

Holds every widget, template and application-level wiring. It reads the
state produced by :mod:`rature.core` and forwards user actions back to it,
never the reverse.
"""

APP_ID = "io.github.vertours.Rature"
