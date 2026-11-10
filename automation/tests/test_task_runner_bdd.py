"""BDD tests for the unified doit task runner."""

import configparser
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from doit.loader import load_tasks
from pytest_bdd import given, parsers, scenarios, then, when

scenarios(str(Path(__file__).resolve().parents[1] / "features" / "task_runner.feature"))


@pytest.fixture
def runner_state() -> dict[str, Any]:
    return {}


@given("the automation task module is loaded")
def load_automation_module(
    dodo_module: ModuleType, runner_state: dict[str, Any]
) -> None:
    tasks = load_tasks(vars(dodo_module))
    runner_state["dodo"] = dodo_module
    runner_state["tasks"] = {task.name: task for task in tasks}


@then(parsers.parse('the default task is "{default_task}" with backend "{backend}"'))
def verify_doit_config(
    runner_state: dict[str, Any], default_task: str, backend: str
) -> None:
    config = runner_state["dodo"].DOIT_CONFIG
    assert config["default_tasks"] == [default_task]
    assert config["backend"] == backend


@then("all expected repository automation tasks are registered")
def verify_expected_tasks(runner_state: dict[str, Any]) -> None:
    expected = {
        "install-projects",
        "test",
        "test-scripts",
        "test-automation",
        "coverage",
        "lint",
        "format-check",
        "typecheck",
        "audit",
        "check-packages",
        "alint",
        "lint-prose",
        "bun-install",
        "docs-lint",
        "actionlint",
        "install-hooks",
        "lint-commit",
        "check-commit-messages",
        "build-release",
        "pre-commit",
        "policy",
        "docs",
        "ci",
    }
    assert expected.issubset(runner_state["tasks"])


@then(parsers.parse('"{task_name}" depends on "{dependency}"'))
def verify_task_dependency(
    runner_state: dict[str, Any], task_name: str, dependency: str
) -> None:
    assert dependency in runner_state["tasks"][task_name].task_dep


@then("composite task groups only depend on registered tasks")
def verify_composite_groups(runner_state: dict[str, Any]) -> None:
    by_name = runner_state["tasks"]
    for group in ("pre-commit", "policy", "docs", "ci"):
        assert set(by_name[group].task_dep).issubset(by_name)
    assert "test-automation" in by_name["ci"].task_dep


class _CasePreservingConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


@given("the repository doit configuration")
def load_doit_cfg(repo_root: Path, runner_state: dict[str, Any]) -> None:
    parser = _CasePreservingConfigParser()
    parser.read(repo_root / "doit.cfg", encoding="utf-8")
    runner_state["doit_parser"] = parser


@when("doit configuration is inspected")
def inspect_doit_config(dodo_module: ModuleType, runner_state: dict[str, Any]) -> None:
    runner_state["dodo"] = dodo_module
    runner_state["doit_config"] = runner_state["doit_parser"]["GLOBAL"]


@then(parsers.parse('dodoFile targets "{dodo_file}" from "{cwd_path}"'))
def verify_doit_cfg_paths(
    runner_state: dict[str, Any], dodo_file: str, cwd_path: str
) -> None:
    config = runner_state["doit_config"]
    assert config["dodoFile"] == dodo_file
    assert config["cwdPath"] == cwd_path


@then("the task module resolves ROOT to the repository root")
def verify_root_resolution(repo_root: Path, runner_state: dict[str, Any]) -> None:
    dodo = runner_state["dodo"]
    assert dodo.ROOT == repo_root
    assert Path(dodo.DOIT_CONFIG["dep_file"]) == repo_root / ".doit.db"


@given("a temporary workspace with generated coverage and distribution artifacts")
def populate_temp_artifacts(tmp_path: Path, runner_state: dict[str, Any]) -> None:
    (tmp_path / "coverage.xml").write_text("<xml/>", encoding="utf-8")
    (tmp_path / ".coverage").write_text("data", encoding="utf-8")
    (tmp_path / "distributions").mkdir()
    (tmp_path / "distributions" / "pkg.whl").write_bytes(b"whl")
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "pkg.whl").write_bytes(b"whl")
    runner_state["workspace"] = tmp_path


@when("the automation clean helpers run")
def run_clean_helpers(dodo_module: ModuleType, runner_state: dict[str, Any]) -> None:
    workspace = runner_state["workspace"]
    dodo_module.clean_coverage(root=workspace)
    dodo_module.clean_distributions(root=workspace)
    dodo_module.clean_dist(root=workspace)


@then("generated coverage and distribution artifacts are removed")
def verify_artifacts_removed(runner_state: dict[str, Any]) -> None:
    workspace = runner_state["workspace"]
    assert not (workspace / "coverage.xml").exists()
    assert not (workspace / ".coverage").exists()
    assert not (workspace / "distributions").exists()
    assert not (workspace / "dist").exists()


@when("doit list runs from the repository root")
def run_doit_list_from_root(repo_root: Path, runner_state: dict[str, Any]) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "doit", "list"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    runner_state["cli_tasks"] = {
        line.split()[0] for line in result.stdout.splitlines() if line.strip()
    }


@then(parsers.parse('the listed tasks include "{first}" and "{second}"'))
def verify_cli_listed_tasks(
    runner_state: dict[str, Any], first: str, second: str
) -> None:
    assert {first, second}.issubset(runner_state["cli_tasks"])
