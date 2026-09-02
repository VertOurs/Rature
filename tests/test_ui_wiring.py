# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 VertOurs
"""Structural checks on ui/ and data/ui/: no gi, source and XML only.

Catches at CI time what only shows up at launch otherwise: a .ui file
missing from the gresource bundle or POTFILES.in, an untranslated
visible string, a @Gtk.Template pointing at a file or child id that
does not exist (Gtk.Template's number one failure mode), or business
logic reaching ui/ through an import ARCHITECTURE.md says only
App should carry.
"""

import ast
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).parent.parent
DATA_UI = REPO / "data" / "ui"
UI_SRC = REPO / "src" / "rature" / "ui"
GRESOURCE_PREFIX = "/io/github/vertours/Rature"

TRANSLATABLE_PROPERTIES = {
    "label",
    "title",
    "subtitle",
    "tooltip-text",
    "placeholder-text",
}

# (file name, property name, text) explicitly allowed to stay untranslated.
TRANSLATABLE_EXCEPTIONS = {
    ("window.ui", "title", "Rature"),  # the app's own name, not a sentence
}

CORE_MODULES = {"rature.core.session", "rature.core.storage", "rature.core.models"}


def _ui_files() -> list[Path]:
    return sorted(DATA_UI.glob("*.ui"))


def test_every_ui_file_is_in_the_gresource_bundle() -> None:
    tree = ET.parse(REPO / "data" / "rature.gresource.xml")
    bundled = {Path(node.text).name for node in tree.iter("file") if node.text}
    missing = {path.name for path in _ui_files()} - bundled
    assert not missing, f".ui files missing from rature.gresource.xml: {missing}"


def test_every_ui_file_is_in_potfiles() -> None:
    entries = {
        line.strip()
        for line in (REPO / "po" / "POTFILES.in")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.startswith("#")
    }
    relative = {path.relative_to(REPO).as_posix() for path in _ui_files()}
    missing = relative - entries
    assert not missing, f".ui files missing from po/POTFILES.in: {missing}"


def _calls_gettext(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            return True
    return False


def test_python_modules_that_call_gettext_are_in_potfiles() -> None:
    entries = {
        line.strip()
        for line in (REPO / "po" / "POTFILES.in")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.startswith("#")
    }
    missing = []
    for path in sorted((REPO / "src" / "rature").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(REPO).as_posix()
        if _calls_gettext(tree) and relative not in entries:
            missing.append(relative)
    assert not missing, f"_() strings not extracted, add to po/POTFILES.in: {missing}"


def test_visible_properties_are_marked_translatable() -> None:
    violations = []
    for ui_path in _ui_files():
        tree = ET.parse(ui_path)
        for prop in tree.iter("property"):
            name = prop.get("name")
            if name not in TRANSLATABLE_PROPERTIES:
                continue
            if prop.get("translatable") == "yes":
                continue
            if (ui_path.name, name, prop.text) in TRANSLATABLE_EXCEPTIONS:
                continue
            violations.append(
                f"{ui_path.name}: {name}={prop.text!r} is not translatable"
            )
    assert not violations, violations


def _is_type_checking(expr: ast.expr) -> bool:
    if isinstance(expr, ast.Name):
        return expr.id == "TYPE_CHECKING"
    if isinstance(expr, ast.Attribute):
        return expr.attr == "TYPE_CHECKING"
    return False


def _template_decorator_resource_path(node: ast.ClassDef) -> str | None:
    for decorator in node.decorator_list:
        if not (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "Template"
        ):
            continue
        for keyword in decorator.keywords:
            if keyword.arg == "resource_path" and isinstance(
                keyword.value, ast.Constant
            ):
                return keyword.value.value
    return None


def _template_class_children(node: ast.ClassDef) -> tuple[str | None, list[str]]:
    gtype_name = None
    child_ids = []
    for item in node.body:
        if not (isinstance(item, ast.Assign) and len(item.targets) == 1):
            continue
        target = item.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "__gtype_name__" and isinstance(item.value, ast.Constant):
            gtype_name = item.value.value
            continue
        call = item.value
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "Child"
        ):
            continue
        child_id = target.id
        if call.args and isinstance(call.args[0], ast.Constant):
            child_id = call.args[0].value
        for keyword in call.keywords:
            if keyword.arg == "id" and isinstance(keyword.value, ast.Constant):
                child_id = keyword.value.value
        child_ids.append(child_id)
    return gtype_name, child_ids


def _template_classes(tree: ast.Module):
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        resource_path = _template_decorator_resource_path(node)
        if resource_path is None:
            continue
        gtype_name, child_ids = _template_class_children(node)
        yield resource_path, gtype_name, child_ids


def test_template_classes_point_to_existing_ui_with_matching_children() -> None:
    violations = []
    for py_path in sorted(UI_SRC.glob("*.py")):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for resource_path, gtype_name, child_ids in _template_classes(tree):
            if not resource_path.startswith(GRESOURCE_PREFIX + "/"):
                violations.append(
                    f"{py_path.name}: resource_path {resource_path!r} "
                    f"outside {GRESOURCE_PREFIX}"
                )
                continue
            relative = resource_path[len(GRESOURCE_PREFIX) + 1 :]
            ui_path = REPO / "data" / relative
            if not ui_path.is_file():
                violations.append(f"{py_path.name}: no such .ui file {relative}")
                continue
            ui_tree = ET.parse(ui_path)
            template = ui_tree.find("template")
            if template is None or template.get("class") != gtype_name:
                violations.append(
                    f"{py_path.name}: {ui_path.name} has no "
                    f"<template class={gtype_name!r}>"
                )
                continue
            ids_in_ui = {node.get("id") for node in ui_tree.iter() if node.get("id")}
            missing = set(child_ids) - ids_in_ui
            if missing:
                violations.append(
                    f"{py_path.name}: Template.Child ids missing from "
                    f"{ui_path.name}: {sorted(missing)}"
                )
    assert not violations, violations


def _bad_core_imports(tree: ast.Module) -> list[str]:
    bad: list[str] = []

    def visit(node: ast.AST, guarded: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.If) and _is_type_checking(child.test):
                for stmt in child.body:
                    visit(stmt, True)
                for stmt in child.orelse:
                    visit(stmt, guarded)
                continue
            if isinstance(child, ast.Import):
                for alias in child.names:
                    if alias.name in CORE_MODULES and not guarded:
                        bad.append(alias.name)
            elif isinstance(child, ast.ImportFrom):
                module = child.module
                if module in CORE_MODULES and not guarded:
                    bad.append(module)
            else:
                visit(child, guarded)

    visit(tree, False)
    return bad


def test_ui_modules_only_import_core_session_storage_models_for_typing() -> None:
    violations = []
    for py_path in sorted(UI_SRC.glob("*.py")):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for module in _bad_core_imports(tree):
            violations.append(f"{py_path.name}: imports {module} outside TYPE_CHECKING")
    assert not violations, violations
