from pathlib import Path

# Verify that the required Alembic configuration files and folders exist.
def test_alembic_configuration_files_exist() -> None:
    assert Path("alembic.ini").is_file()
    assert Path("alembic/env.py").is_file()
    assert Path("alembic/versions").is_dir()


# Verify that Alembic is connected to the project's SQLAlchemy metadata.
def test_alembic_env_imports_project_metadata() -> None:
    env_py = Path("alembic/env.py").read_text()

    assert "from app.db.base import metadata" in env_py
    assert "target_metadata = metadata" in env_py

