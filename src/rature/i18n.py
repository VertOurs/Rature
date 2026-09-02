# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""Locale helpers for the launcher.

No gi import: like rature.main, this must stay importable on an
interpreter without PyGObject.
"""

from __future__ import annotations

import locale
from collections.abc import Callable, Mapping

# gettext's own precedence for choosing the message language.
_MESSAGE_ENV = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
_NEUTRAL = frozenset({"", "C", "POSIX", "C.UTF-8", "C.utf8"})


def message_language(environ: Mapping[str, str]) -> str | None:
    """The language gettext will translate into, in its own precedence order.

    ``LANGUAGE`` (a colon-separated list) wins, then ``LC_ALL``,
    ``LC_MESSAGES``, ``LANG``. Returns the language-and-region part
    (``fr_FR``, or just ``fr``), codeset and ``@modifier`` stripped, or
    ``None`` when nothing but the C locale is set.
    """
    for name in _MESSAGE_ENV:
        value = environ.get(name, "")
        if value and value not in _NEUTRAL:
            first = value.split(":", 1)[0]
            return first.split(".", 1)[0].split("@", 1)[0] or None
    return None


def align_time_locale(
    *,
    environ: Mapping[str, str],
    setlocale: Callable[[int, str], str] = locale.setlocale,
) -> str | None:
    """Point ``LC_TIME`` at the interface language so dates match it.

    ROADMAP chantier 4 and SPECIFICATION.md §3.8: ``strftime`` month and
    weekday names must be in the interface language.
    ``setlocale(LC_ALL, "")`` follows ``LC_TIME``/``LANG`` and ignores
    ``LANGUAGE``, so a machine with ``LANGUAGE=fr`` and
    ``LC_TIME=en_US.UTF-8`` shows a French interface with English dates.

    Retry ``LC_TIME`` with the message language's usual locale names. If
    none is installed, leave ``LC_TIME`` as it was: best effort, as the
    spec allows. Returns the locale name that took, or ``None``.
    """
    lang = message_language(environ)
    if lang is None:
        return None
    for name in (
        locale.normalize(f"{lang}.UTF-8"),
        lang,
        locale.normalize(lang),
    ):
        try:
            return setlocale(locale.LC_TIME, name)
        except locale.Error:
            continue
    return None
