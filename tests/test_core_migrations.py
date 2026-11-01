# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""The migration base: version checks, the step loop, and the wiring in load."""

import copy
import json
import logging
import os
import stat
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


def test_version_four_is_current() -> None:
    assert CURRENT_VERSION == 4


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
    migrated = migrate(copy.deepcopy(V2_MAIN), target=3)
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
    migrated = migrate(copy.deepcopy(V2_ARCHIVE), target=3)
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


# Step 3 -> 4 alone, on version 3 files as 1.7.1 wrote them. A task and
# a reserve item are marked, to check the 1.7.0 field survives untouched.

V3_MAIN = {
    **copy.deepcopy(V2_MAIN),
    "version": 3,
    "tasks": [{**task, "priority": task["id"] == "t2"} for task in V2_MAIN["tasks"]],
    "deletions": _with_priority(V2_MAIN["deletions"]),
    "reserve": [{**item, "priority": True} for item in V2_MAIN["reserve"]],
}

V3_ARCHIVE = {
    key: copy.deepcopy(value)
    for key, value in V3_MAIN.items()
    if key not in ("reserve", "recurring")
}


def test_a_version_3_main_file_gains_an_empty_tomorrow_list() -> None:
    original = copy.deepcopy(V3_MAIN)
    migrated = migrate(copy.deepcopy(V3_MAIN))
    assert migrated == {**original, "version": 4, "tomorrow": []}


def test_the_tomorrow_migration_leaves_its_input_untouched() -> None:
    data = copy.deepcopy(V3_MAIN)
    migrate(data)
    assert data == V3_MAIN


def test_a_version_3_archive_only_gets_the_version_bump() -> None:
    migrated = migrate(copy.deepcopy(V3_ARCHIVE))
    assert migrated == {**V3_ARCHIVE, "version": 4}
    assert "tomorrow" not in migrated


def test_a_version_3_file_opens_with_nothing_prepared(tmp_path: Path) -> None:
    (tmp_path / "data.json").write_text(json.dumps(V3_MAIN), encoding="utf-8")
    monday = datetime(2026, 8, 24, 18, 0, tzinfo=PARIS)
    app = App.open(tmp_path, clock=lambda: monday)

    assert app.startup is StartupOutcome.LOADED
    assert app.session.tomorrow == []
    assert [task.id for task in app.session.day.tasks] == ["t1", "t2"]
    assert [task.priority for task in app.session.day.tasks] == [False, True]
    assert app.session.reserve[0].priority
    app.add("trigger a save")
    on_disk = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert on_disk["version"] == 4
    assert on_disk["tomorrow"] == []


# Every step chained, from a version 1 file.


def test_a_version_1_main_file_migrates_to_4_with_no_loss() -> None:
    original = copy.deepcopy(V1_MAIN)
    assert migrate(copy.deepcopy(V1_MAIN)) == {
        **original,
        "version": 4,
        "tasks": _with_priority(original["tasks"]),
        "deletions": _with_priority(original["deletions"]),
        "reserve": _with_priority(original["reserve"]),
        "tomorrow": [],
        "recurring": [
            {
                "id": "w1",
                "text": "water plants",
                "weekdays": [1],
                "every_other_week_from": None,
            }
        ],
    }


@pytest.mark.parametrize("archive", [V1_ARCHIVE, V2_ARCHIVE, V3_ARCHIVE])
def test_an_older_archive_file_loads(tmp_path: Path, archive: dict) -> None:
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "2026-08-24.json").write_text(
        json.dumps(archive), encoding="utf-8"
    )
    day = storage.load_archive(date(2026, 8, 24), data_dir=tmp_path)
    # setdefault: a version 3 archive already carries its priorities.
    expected = {
        **archive,
        "version": 4,
        "tasks": [{"priority": False, **task} for task in archive["tasks"]],
        "deletions": [{"priority": False, **e} for e in archive["deletions"]],
    }
    del expected["version"]
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

    app.add("first gesture")  # what writes the rollover (§2.5)
    archived = storage.load_archive(date(2026, 8, 24), data_dir=tmp_path)
    assert [task.id for task in archived.tasks] == ["t1", "t2"]
    on_disk = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert on_disk["version"] == 4
    assert on_disk["tomorrow"] == []
    assert on_disk["recurring"][0]["every_other_week_from"] is None
    assert not any(item["priority"] for item in on_disk["reserve"])


# SPECIFICATION.md §2.7.10: a load that migrates first keeps the file as
# it was on disk, byte for byte, in data.json.v<N>.bak.


def _write_raw(tmp_path: Path, data: dict) -> bytes:
    # Indented and non-ASCII on purpose: the backup must match these bytes,
    # not a re-serialisation of the loaded data.
    raw = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")
    (tmp_path / "data.json").write_bytes(raw)
    return raw


@pytest.mark.parametrize(
    ("data", "version"), [(V1_MAIN, 1), (V2_MAIN, 2), (V3_MAIN, 3)]
)
def test_a_migrating_load_backs_up_the_file_byte_for_byte(
    tmp_path: Path, data: dict, version: int
) -> None:
    raw = _write_raw(
        tmp_path, {**data, "reserve": [{**data["reserve"][0], "text": "vélo"}]}
    )
    load(data_dir=tmp_path)
    backup = tmp_path / f"data.json.v{version}.bak"
    assert backup.read_bytes() == raw
    assert (tmp_path / "data.json").read_bytes() == raw
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600


def test_a_current_version_load_makes_no_backup(tmp_path: Path) -> None:
    save(Store(day=Day(date=date(2026, 8, 24))), data_dir=tmp_path)
    load(data_dir=tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_an_existing_backup_is_kept_and_not_doubled(tmp_path: Path) -> None:
    _write_raw(tmp_path, V1_MAIN)
    backup = tmp_path / "data.json.v1.bak"
    backup.write_bytes(b"the true original")
    load(data_dir=tmp_path)
    assert backup.read_bytes() == b"the true original"
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "data.json",
        "data.json.v1.bak",
    ]


def test_an_unreadable_old_file_is_not_backed_up(tmp_path: Path) -> None:
    # Version 1, but no date: the load fails and the file stays untouched.
    _write_raw(tmp_path, {key: v for key, v in V1_MAIN.items() if key != "date"})
    with pytest.raises((KeyError, ValueError)):
        load(data_dir=tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores permissions")
def test_a_failed_backup_raises_and_leaves_nothing_behind(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    raw = _write_raw(tmp_path, V1_MAIN)
    tmp_path.chmod(0o500)
    try:
        with (
            caplog.at_level(logging.ERROR, logger="rature.core.storage"),
            pytest.raises(OSError),
        ):
            load(data_dir=tmp_path)
    finally:
        tmp_path.chmod(0o700)
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]
    assert (tmp_path / "data.json").read_bytes() == raw
    assert str(tmp_path / "data.json") in caplog.text


def test_a_backup_link_lost_to_a_race_keeps_the_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Another process creates the backup between the exists() check and
    # the link: os.link refuses to overwrite it, and the load still succeeds.
    _write_raw(tmp_path, V1_MAIN)
    backup = tmp_path / "data.json.v1.bak"
    real_link = os.link

    def racing_link(src: str, dst: str) -> None:
        backup.write_bytes(b"the winner")
        real_link(src, dst)

    monkeypatch.setattr(os, "link", racing_link)
    load(data_dir=tmp_path)
    assert backup.read_bytes() == b"the winner"
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "data.json",
        "data.json.v1.bak",
    ]


def test_the_backup_is_logged_with_its_path_only(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _write_raw(tmp_path, V1_MAIN)
    with caplog.at_level(logging.INFO, logger="rature.core.storage"):
        load(data_dir=tmp_path)
    assert str(tmp_path / "data.json.v1.bak") in caplog.text
    assert "call the bank" not in caplog.text


def test_opening_an_old_file_keeps_the_original_beside_the_rewritten_one(
    tmp_path: Path,
) -> None:
    raw = _write_raw(tmp_path, V1_MAIN)
    app = App.open(tmp_path, clock=lambda: datetime(2026, 8, 24, 18, 0, tzinfo=PARIS))
    app.add("one more")
    assert (tmp_path / "data.json.v1.bak").read_bytes() == raw
    on_disk = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert on_disk["version"] == CURRENT_VERSION


# Strict reading after migration (test_core_validation.py): the
# hand-written files of each version above load in full, not just the
# keys the earlier tests look at.


@pytest.mark.parametrize("main", [V1_MAIN, V2_MAIN, V3_MAIN], ids=["v1", "v2", "v3"])
def test_an_older_main_file_passes_the_strict_reading(
    tmp_path: Path, main: dict
) -> None:
    (tmp_path / "data.json").write_text(json.dumps(main), encoding="utf-8")
    store = load(data_dir=tmp_path)
    assert [task.id for task in store.day.tasks] == ["t1", "t2"]
    assert [item.id for item in store.reserve] == ["r1"]
    assert [item.id for item in store.recurring] == ["w1"]
    assert store.tomorrow == []
