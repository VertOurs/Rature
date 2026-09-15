# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The stderr handler and RATURE_LOG_LEVEL (ROADMAP chantier 6)."""

from __future__ import annotations

import io
import logging

import pytest

from rature.logging_setup import ENV_VAR, LOGGER_NAME, configure


@pytest.fixture(autouse=True)
def _reset_rature_logger():
    logger = logging.getLogger(LOGGER_NAME)
    handlers_before = list(logger.handlers)
    level_before = logger.level
    yield
    logger.handlers[:] = handlers_before
    logger.setLevel(level_before)


def test_defaults_to_info() -> None:
    configure(environ={})
    assert logging.getLogger(LOGGER_NAME).level == logging.INFO


def test_reads_the_level_from_the_environment() -> None:
    configure(environ={ENV_VAR: "DEBUG"})
    assert logging.getLogger(LOGGER_NAME).level == logging.DEBUG


def test_the_level_is_case_insensitive() -> None:
    configure(environ={ENV_VAR: "warning"})
    assert logging.getLogger(LOGGER_NAME).level == logging.WARNING


def test_an_unknown_level_falls_back_to_info() -> None:
    configure(environ={ENV_VAR: "not-a-level"})
    assert logging.getLogger(LOGGER_NAME).level == logging.INFO


def test_writes_to_the_given_stream() -> None:
    stream = io.StringIO()
    configure(environ={}, stream=stream)
    logging.getLogger("rature.somewhere").info("hello")
    assert "hello" in stream.getvalue()


def test_a_second_call_replaces_the_handler_instead_of_stacking_one() -> None:
    configure(environ={}, stream=io.StringIO())
    configure(environ={}, stream=io.StringIO())
    assert len(logging.getLogger(LOGGER_NAME).handlers) == 1


def test_defaults_to_the_real_environment_when_none_is_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VAR, "ERROR")
    configure()
    assert logging.getLogger(LOGGER_NAME).level == logging.ERROR
