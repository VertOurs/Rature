# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs

"""The long-form date: Day view and Archives titles, the Statistics Day
column and the clipboard copy (SPECIFICATION.md §3.8).

No gi: gettext and strftime only. strftime supplies the weekday and month
names from LC_TIME; the format itself comes from the catalogue, since
word order and connecting words ("jueves, 29 de octubre") differ by
language.
"""

from __future__ import annotations

from gettext import gettext as _
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

# The catalogue's format only reads right when strftime's names are in the
# same language. Without a matching locale installed (common in a Flatpak,
# which ships the system's languages only), "%A, %-d de %B" would wrap
# English names: "Thursday, 29 de October". The source format has no
# connecting words, so it stays in one language whatever LC_TIME is.
_use_catalogue = True


def use_catalogue_format(enabled: bool) -> None:
    """Whether dates take their format from the catalogue.

    The launcher passes whether LC_TIME could follow the interface
    language (rature.i18n.align_time_locale).
    """
    global _use_catalogue
    _use_catalogue = enabled


def long_date(day: date) -> str:
    """The date with its weekday, in the interface language's own order."""
    # Translators: a strftime format for a long date with its weekday,
    # e.g. "Thursday 29 October". %A is the weekday, %d the day of the
    # month, %B the month; the names come out in your language. Reorder
    # them and add words as your language needs; %-d drops the leading
    # zero. Do not translate the codes themselves.
    return day.strftime(_("%A %d %B") if _use_catalogue else "%A %d %B")
