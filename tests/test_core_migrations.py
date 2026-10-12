# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The migration base: version checks, the step loop, and the wiring in load."""

import copy
import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from rature.core import migrations, storage
from rature.core.app import App, StartupOutcome
from rature.core.migrations import CURRENT_VERSION, FutureVersionError, migrate
from rature.core.models import Origin
from rature.core.session import Day
from rature.core.storage import Store, load, save

PARIS = timezone(timedelta(hours=2))


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


def test_an_applied_step_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    def one_to_two(data: dict) -> dict:
        return {**data, "version": 2}

    with caplog.at_level(logging.INFO, logger="rature.core.migrations"):
        migrate({"version": 1}, target=2, registry={1: one_to_two})
    assert "1" in caplog.text
    assert "2" in caplog.text


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
    # An unused version number: the real steps must survive this test.
    @migrations._migration(99)
    def _fake(data: dict) -> dict:
        return {**data, "version": 100}

    try:
        assert migrations._MIGRATIONS[99] is _fake
    finally:
        del migrations._MIGRATIONS[99]


def test_load_runs_migrations_on_the_raw_file(tmp_path: Path) -> None:
    save(Store(day=Day(date=date(2026, 8, 24))), data_dir=tmp_path)
    # A current-version file: migrate is a no-op, load succeeds.
    assert load(data_dir=tmp_path).day.date == date(2026, 8, 24)


# A version 1 main file as 1.5.0 wrote it, every kind of entry present.
# 2026-08-24 is a Monday; the template is due on Tuesdays.
V1_MAIN = {
    "version": 1,
    "date": "2026-08-24",
    "counter": 4,
    "locked": False,
    "tasks": [
        {
            "id": "t1",
            "num": 1,
            "text": "write the tests",
            "done": True,
            "done_at": "2026-08-24T14:32:07+02:00",
            "origin": "day",
            "source_id": None,
            "source_created": None,
            "template_id": None,
        },
        {
            "id": "t2",
            "num": 2,
            "text": "call the bank",
            "done": False,
            "done_at": None,
            "origin": "reserve",
            "source_id": "r9",
            "source_created": "2026-08-20",
            "template_id": None,
        },
    ],
    "deletions": [
        {
            "id": "t3",
            "num": 3,
            "text": "never mind",
            "origin": "day",
            "source_id": None,
            "source_created": None,
            "template_id": None,
            "done": False,
            "done_at": None,
            "index": 2,
            "deleted_at": "2026-08-24T15:00:00+02:00",
        }
    ],
    "reserve": [{"id": "r1", "text": "fix the bike", "created": "2026-08-21"}],
    "recurring": [{"id": "w1", "text": "water plants", "weekdays": [1]}],
}

# A version 1 archive: a day only, no reserve and no recurring key.
V1_ARCHIVE = {
    key: copy.deepcopy(value)
    for key, value in V1_MAIN.items()
    if key not in ("reserve", "recurring")
}


def test_version_three_is_current() -> None:
    assert CURRENT_VERSION == 3


def _with_priority(entries: list[dict]) -> list[dict]:
    return [{**entry, "priority": False} for entry in entries]


# Step 1 -> 2 alone: every recurring template gains every_other_week_from.


def test_a_version_1_main_file_loses_nothing() -> None:
    original = copy.deepcopy(V1_MAIN)
    migrated = migrate(copy.deepcopy(V1_MAIN), target=2)
    expected = {
        **original,
        "version": 2,
        "recurring": [
            {
                "id": "w1",
                "text": "water plants",
                "weekdays": [1],
                "every_other_week_from": None,
            }
        ],
    }
    assert migrated == expected


def test_the_migration_leaves_its_input_untouched() -> None:
    data = copy.deepcopy(V1_MAIN)
    migrate(data)
    assert data == V1_MAIN


def test_a_version_1_archive_only_gets_the_version_bump() -> None:
    migrated = migrate(copy.deepcopy(V1_ARCHIVE), target=2)
    assert migrated == {**V1_ARCHIVE, "version": 2}


def test_a_non_object_template_is_rejected() -> None:
    with pytest.raises(TypeError):
        migrate({**V1_MAIN, "recurring": ["water plants"]})


# Step 2 -> 3 alone, on version 2 files as 1.6.0 wrote them. The template
# is every other week, to check the 1.6.0 field survives untouched.

V2_MAIN = {
    **copy.deepcopy(V1_MAIN),
    "version": 2,
    "recurring": [
        {
            "id": "w1",
            "text": "water plants",
            "weekdays": [1],
            "every_other_week_from": "2026-08-24",
        }
    ],
}

V2_ARCHIVE = {**copy.deepcopy(V1_ARCHIVE), "version": 2}


def test_a_version_2_main_file_loses_nothing() -> None:
    original = copy.deepcopy(V2_MAIN)
    migrated = migrate(copy.deepcopy(V2_MAIN))
    expected = {
        **original,
        "version": 3,
        "tasks": _with_priority(original["tasks"]),
        "deletions": _with_priority(original["deletions"]),
        "reserve": _with_priority(original["reserve"]),
    }
    assert migrated == expected


def test_the_priority_migration_leaves_its_input_untouched() -> None:
    data = copy.deepcopy(V2_MAIN)
    migrate(data)
    assert data == V2_MAIN


def test_a_version_2_archive_gains_priority_but_no_reserve() -> None:
    original = copy.deepcopy(V2_ARCHIVE)
    migrated = migrate(copy.deepcopy(V2_ARCHIVE))
    assert migrated == {
        **original,
        "version": 3,
        "tasks": _with_priority(original["tasks"]),
        "deletions": _with_priority(original["deletions"]),
    }
    assert "reserve" not in migrated


def test_a_non_object_reserve_item_is_rejected() -> None:
    with pytest.raises(TypeError):
        migrate({**V2_MAIN, "reserve": ["fix the bike"]})


def test_a_version_2_file_opens_with_nothing_marked(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text(json.dumps(V2_MAIN), encoding="utf-8")
    monday = datetime(2026, 8, 24, 18, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=lambda: monday)

    assert app.startup is StartupOutcome.LOADED
    assert [task.id for task in app.session.day.tasks] == ["t1", "t2"]
    assert [task.num for task in app.session.day.tasks] == [1, 2]
    assert not any(task.priority for task in app.session.day.tasks)
    assert [item.id for item in app.session.reserve] == ["r1"]
    assert not app.session.reserve[0].priority
    assert not app.session.day.deletions[0].priority
    assert app.session.recurring[0].every_other_week_from == date(2026, 8, 24)


# Both steps chained, from a version 1 file.


def test_a_version_1_main_file_migrates_to_3_with_no_loss() -> None:
    original = copy.deepcopy(V1_MAIN)
    assert migrate(copy.deepcopy(V1_MAIN)) == {
        **original,
        "version": 3,
        "tasks": _with_priority(original["tasks"]),
        "deletions": _with_priority(original["deletions"]),
        "reserve": _with_priority(original["reserve"]),
        "recurring": [
            {
                "id": "w1",
                "text": "water plants",
                "weekdays": [1],
                "every_other_week_from": None,
            }
        ],
    }


@pytest.mark.parametrize("archive", [V1_ARCHIVE, V2_ARCHIVE])
def test_an_older_archive_file_loads(tmp_path: Path, archive: dict) -> None:
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "2026-08-24.json").write_text(
        json.dumps(archive), encoding="utf-8"
    )
    day = storage.load_archive(date(2026, 8, 24), data_dir=tmp_path)
    expected = {
        **archive,
        "version": 3,
        "tasks": _with_priority(archive["tasks"]),
        "deletions": _with_priority(archive["deletions"]),
    }
    assert Day.from_dict(expected) == day
    assert [task.id for task in day.tasks] == ["t1", "t2"]
    assert [entry.id for entry in day.deletions] == ["t3"]


def test_a_version_1_file_is_migrated_and_injects_as_before(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text(json.dumps(V1_MAIN), encoding="utf-8")
    tuesday = datetime(2026, 8, 25, 9, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=lambda: tuesday)

    assert app.startup is StartupOutcome.LOADED
    (template,) = app.session.recurring
    assert (template.id, template.text, template.weekdays) == (
        "w1",
        "water plants",
        [1],
    )
    assert template.every_other_week_from is None
    injected = [t for t in app.session.day.tasks if t.origin == Origin.RECURRING]
    assert [(t.text, t.template_id) for t in injected] == [("water plants", "w1")]
    # The rollover sent the unfinished reserve task back, as in version 1.
    assert {item.id for item in app.session.reserve} == {"r1", "r9"}

    archived = storage.load_archive(date(2026, 8, 24), data_dir=tmp_path)
    assert [task.id for task in archived.tasks] == ["t1", "t2"]
    on_disk = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert on_disk["version"] == 3
    assert on_disk["recurring"][0]["every_other_week_from"] is None
    assert not any(item["priority"] for item in on_disk["reserve"])
