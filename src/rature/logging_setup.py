# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Attaches the one log handler Rature uses: stderr, level from the environment.

No gi import: like rature.main and rature.i18n, this must stay importable
on an interpreter without PyGObject.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Mapping
from typing import TextIO

LOGGER_NAME = "rature"
ENV_VAR = "RATURE_LOG_LEVEL"
DEFAULT_LEVEL = "INFO"


def configure(
    *,
    environ: Mapping[str, str] | None = None,
    stream: TextIO = sys.stderr,
) -> None:
    """Attach a stderr handler to the "rature" logger tree.

    Every module logs through ``logging.getLogger(__name__)``, a child of
    "rature", so configuring the level and handler here once is enough for
    all of them. The level comes from RATURE_LOG_LEVEL (DEBUG, INFO,
    WARNING, ERROR or CRITICAL, case-insensitive); an unset or unknown
    value falls back to INFO rather than raising, since a typo in the
    environment must not stop the application from starting.

    Idempotent: a second call replaces the handler instead of stacking a
    duplicate, so re-running it (tests, or a future preferences reload)
    does not double every line.
    """
    env = environ if environ is not None else os.environ
    raw_level = env.get(ENV_VAR, DEFAULT_LEVEL).upper()
    level = logging.getLevelNamesMapping().get(raw_level, logging.INFO)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
