"""Foundation tests for the AI Retail Analytics Platform (Sprint 1)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_structure() -> None:
    required_files = [
        "ai/__init__.py",
        "backend/__init__.py",
        "tests/test_project.py",
        "pyproject.toml",
        "requirements.txt",
        ".gitignore",
        ".env.example",
        "README.md",
        "AGENTS.md",
    ]
    missing = [f for f in required_files if not (ROOT / f).exists()]
    assert not missing, f"Missing required files: {missing}"


def test_required_directories() -> None:
    required_dirs = [
        "ai",
        "backend",
        "frontend",
        "config",
        "data",
        "models",
        "recordings",
        "scripts",
        "tests",
        "docker",
        "docs",
    ]
    missing = [d for d in required_dirs if not (ROOT / d).is_dir()]
    assert not missing, f"Missing required directories: {missing}"


def test_python_environment() -> None:
    assert sys.version_info >= (3, 11), (
        f"Python >= 3.11 is required, found {sys.version.split()[0]}"
    )


def test_packages_are_importable() -> None:
    import ai
    import backend

    assert ai.__name__ == "ai"
    assert backend.__name__ == "backend"


def test_env_example_uses_empty_placeholders() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in ("DATABASE_URL", "CAMERA_RTSP_URL", "DEEPSEEK_API_KEY"):
        assert f"{key}=" in text, f"{key} must appear as an empty placeholder"
        assert f"{key}=http" not in text
        assert f"{key}=postgres" not in text
