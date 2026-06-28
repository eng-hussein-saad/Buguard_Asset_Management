from pathlib import Path


def test_readme_documents_phase7_submission_workflows() -> None:
    readme = Path("README.md").read_text().lower()

    for phrase in (
        "analysis",
        "certificate lifecycle",
        "seed",
        "authentication",
        "rate limit",
        "known tradeoffs",
        "public registration",
    ):
        assert phrase in readme


def test_env_example_contains_analysis_placeholders() -> None:
    env_example = Path(".env.example").read_text()

    for key in (
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "CACHE_URL",
        "RATE_LIMIT_AI_ANALYSIS_ATTEMPTS",
        "ANALYSIS_PROVIDER",
        "ANALYSIS_MODEL",
        "ANALYSIS_API_KEY",
        "ANALYSIS_BASE_URL",
    ):
        assert key in env_example
