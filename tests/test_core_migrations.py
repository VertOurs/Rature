# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The migration base: version checks, the step loop, and the wiring in load."""

from datetime import date
from pathlib import Path

import pytest

from rature.core import migrations
from rature.core.migrations import CURRENT_VERSION, FutureVersionError, migrate
from rature.core.session import Day
from rature.core.storage import Store, load, save


def test_current_version_data_passes_through_unchanged() -> None:
    data = {"version": CURRENT_VERSION, "date": "2026-08-24"}
    assert migrate(data) is data


def test_missing_version_is_rejected() -> None:
    with pytest.raises(ValueError):
        migrate({"date": "2026-08-24"})


@pytest.mark.parametrize("not_an_object", [[], ["version", 1], "1", 1, None])
def test_a_non_object_top_level_is_rejected(not_an_object: object) -> None:
    with pytest.raises(ValueError):
        migrate(not_an_object)


def test_a_non_integer_version_is_rejected() -> None:
    with pytest.raises(ValueError):
        migrate({"version": "1"})


def test_a_boolean_version_is_rejected() -> None:
    with pytest.raises(ValueError):
        migrate({"version": True})


def test_a_version_below_one_is_rejected() -> None:
    with pytest.raises(ValueError):
        migrate({"version": 0})


def test_a_future_version_is_rejected() -> None:
    with pytest.raises(FutureVersionError):
        migrate({"version": CURRENT_VERSION + 1})


def test_a_registered_step_is_applied() -> None:
    def one_to_two(data: dict) -> dict:
        return {**data, "version": 2, "added": True}

    result = migrate({"version": 1}, target=2, registry={1: one_to_two})
    assert result == {"version": 2, "added": True}


def test_steps_run_in_order_up_to_the_target() -> None:
    trail: list[int] = []

    def step(to: int):
        def run(data: dict) -> dict:
            trail.append(to)
            return {**data, "version": to}

        return run

    migrate({"version": 1}, target=3, registry={1: step(2), 2: step(3)})
    assert trail == [2, 3]


def test_a_missing_step_is_rejected() -> None:
    with pytest.raises(ValueError):
        migrate({"version": 1}, target=2, registry={})


def test_a_step_that_does_not_advance_the_version_is_rejected() -> None:
    with pytest.raises(RuntimeError):
        migrate({"version": 1}, target=2, registry={1: lambda data: data})


def test_a_step_that_drops_the_version_is_rejected() -> None:
    with pytest.raises(RuntimeError):
        migrate({"version": 1}, target=2, registry={1: lambda _: {}})


def test_the_decorator_registers_a_step() -> None:
    @migrations._migration(1)
    def _fake(data: dict) -> dict:
        return {**data, "version": 2}

    try:
        assert migrations._MIGRATIONS[1] is _fake
    finally:
        del migrations._MIGRATIONS[1]


def test_load_runs_migrations_on_the_raw_file(tmp_path: Path) -> None:
    save(Store(day=Day(date=date(2026, 8, 24))), data_dir=tmp_path)
    # A version 1 file: migrate is a no-op, load succeeds.
    assert load(data_dir=tmp_path).day.date == date(2026, 8, 24)
