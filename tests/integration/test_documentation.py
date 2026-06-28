from pathlib import Path


def test_readme_documents_phase_6_operations() -> None:
    """Verify README covers local checks, CI, seeded users, limits, and cache."""
    readme = Path("README.md").read_text()

    for expected in (
        "uv sync --all-groups",
        "docker compose up -d db redis",
        "uv run ruff check app tests",
        "uv run pytest",
        "uv run mypy app",
        "GitHub Actions",
        "admin@example.com",
        "5 login attempts",
        "10 refresh attempts",
        "10 bulk import attempts",
        "future AI analysis",
        "organization-scoped cache",
        "graceful fallback",
    ):
        assert expected in readme


def test_new_runtime_keys_are_documented() -> None:
    """Verify every Phase 6 runtime key appears in env and README docs."""
    env_example = Path(".env.example").read_text()
    readme = Path("README.md").read_text()

    for key in (
        "CACHE_URL",
        "CACHE_TTL_SECONDS",
        "RATE_LIMIT_WINDOW_SECONDS",
        "RATE_LIMIT_LOGIN_ATTEMPTS",
        "RATE_LIMIT_REFRESH_ATTEMPTS",
        "RATE_LIMIT_BULK_IMPORT_ATTEMPTS",
        "RATE_LIMIT_AI_ANALYSIS_ATTEMPTS",
    ):
        assert key in env_example
        assert key in readme
