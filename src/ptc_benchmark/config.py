from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def project_root(start: str | Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "src" / "ptc_benchmark").exists():
            return candidate
    raise FileNotFoundError("Could not locate the programmatic_tool_calling_demo project root")


def load_local_environment(root: str | Path | None = None) -> Path:
    resolved = project_root(root)
    load_dotenv(resolved / ".env.local", override=False)
    return resolved


def configured_model(default: str = "gpt-5.6") -> str:
    return os.getenv("OPENAI_MODEL", default)


def require_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.local.example to .env.local and add a key."
        )
