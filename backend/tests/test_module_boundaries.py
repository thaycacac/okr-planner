"""Scheduler, calendar and exporters must stay pure so they remain deterministic and testable
offline."""

import ast
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"

FORBIDDEN = {
    "scheduler": ("app.planner_llm", "app.persistence", "app.api", "fastapi", "sqlalchemy"),
    "calendar": ("app.planner_llm", "app.persistence", "app.api", "app.scheduler", "fastapi"),
    "domain": ("app.", "fastapi", "sqlalchemy"),
    "exporters": (
        "app.planner_llm",
        "app.persistence",
        "app.api",
        "app.services",
        "fastapi",
        "sqlalchemy",
    ),
}


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


@pytest.mark.parametrize("package", sorted(FORBIDDEN))
def test_package_does_not_import_forbidden_layers(package: str) -> None:
    allowed_self = f"app.{package}"
    violations = [
        f"{path.relative_to(APP_DIR)} imports {name}"
        for path in (APP_DIR / package).rglob("*.py")
        for name in _imports(path)
        if name.startswith(FORBIDDEN[package]) and not name.startswith(allowed_self)
    ]
    assert not violations, violations
