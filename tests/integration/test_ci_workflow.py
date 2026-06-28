from pathlib import Path


def _workflow_text() -> str:
    """Return the quality workflow text for structural assertions."""
    return Path(".github/workflows/quality.yml").read_text()


def test_quality_workflow_runs_required_checks() -> None:
    """Verify CI installs locked dependencies and exposes named check steps."""
    workflow = _workflow_text()

    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert "python-version: \"3.13\"" in workflow
    assert "uv sync --locked --all-groups" in workflow
    assert "uv run ruff check app tests" in workflow
    assert "uv run pytest" in workflow
    assert "uv run mypy app" in workflow
    assert "Run ruff lint" in workflow
    assert "Run pytest" in workflow


def test_ci_commands_match_documented_local_commands() -> None:
    """Verify CI and documentation name the same local quality commands."""
    workflow = _workflow_text()
    readme = Path("README.md").read_text()
    quickstart = Path("specs/006-test-ci-rate-limits/quickstart.md").read_text()

    for command in (
        "uv run ruff check app tests",
        "uv run pytest",
        "uv run mypy app",
    ):
        assert command in workflow
        assert command in readme
        assert command in quickstart
