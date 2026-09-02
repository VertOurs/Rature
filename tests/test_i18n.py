# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The launcher's locale helpers (src/rature.in uses these)."""

import locale

from rature.i18n import align_time_locale, message_language


def test_message_language_prefers_language_over_lc_and_lang() -> None:
    env = {"LANGUAGE": "fr_FR:fr:en", "LC_ALL": "de_DE.UTF-8", "LANG": "en_US.UTF-8"}
    assert message_language(env) == "fr_FR"


def test_message_language_walks_the_gettext_chain() -> None:
    assert message_language({"LC_ALL": "de_DE.UTF-8"}) == "de_DE"
    assert message_language({"LC_MESSAGES": "es_ES.UTF-8"}) == "es_ES"
    assert message_language({"LANG": "it_IT.UTF-8@euro"}) == "it_IT"


def test_message_language_strips_codeset_and_modifier() -> None:
    assert message_language({"LANG": "pt_BR.ISO8859-1"}) == "pt_BR"


def test_message_language_is_none_for_the_c_locale_or_nothing() -> None:
    assert message_language({}) is None
    assert message_language({"LC_ALL": "C", "LANG": "POSIX"}) is None
    assert message_language({"LANGUAGE": ""}) is None


def test_align_time_locale_sets_lc_time_to_the_message_language() -> None:
    seen = []

    def fake_setlocale(category: int, name: str) -> str:
        seen.append((category, name))
        if name == "fr_FR.UTF-8":
            return name
        raise locale.Error(name)

    got = align_time_locale(environ={"LANGUAGE": "fr"}, setlocale=fake_setlocale)
    assert got == "fr_FR.UTF-8"
    assert (locale.LC_TIME, "fr_FR.UTF-8") in seen


def test_align_time_locale_does_nothing_without_a_message_language() -> None:
    seen = []
    result = align_time_locale(
        environ={"LC_ALL": "C"},
        setlocale=lambda category, name: seen.append((category, name)),
    )
    assert result is None
    assert seen == []


def test_align_time_locale_gives_up_when_no_variant_is_installed() -> None:
    def always_fails(category: int, name: str) -> str:
        raise locale.Error(name)

    assert align_time_locale(environ={"LANGUAGE": "xx"}, setlocale=always_fails) is None
