from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


DEFAULT_MODEL = "gpt-5.5"
DEFAULT_BASE_URL = "https://newapi.lxhei.xyz/v1"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_ENV_FILES = (
    Path(__file__).resolve().parents[1] / ".env",
    Path(__file__).resolve().parents[3] / ".env",
)


@dataclass(frozen=True)
class LLMConfig:
    model: str
    base_url: str
    api_key: str | None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


def get_llm_config(env_file: str | Path | None = None) -> LLMConfig:
    file_values = _read_env_values(env_file) if env_file else _read_first_existing_env(DEFAULT_ENV_FILES)
    return LLMConfig(
        model=_config_value("OPENAI_MODEL", file_values) or DEFAULT_MODEL,
        base_url=_config_value("OPENAI_BASE_URL", file_values) or DEFAULT_BASE_URL,
        api_key=_config_value("OPENAI_API_KEY", file_values),
        timeout_seconds=_float_env(
            _config_value("OPENAI_TIMEOUT_SECONDS", file_values),
            DEFAULT_TIMEOUT_SECONDS,
        ),
    )


def _read_first_existing_env(paths: tuple[Path, ...]) -> dict[str, str]:
    for path in paths:
        values = _read_env_values(path)
        if values:
            return values
    return {}


def _read_env_values(path: str | Path) -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists() or not env_path.is_file():
        return {}

    values = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _clean_env_value(value)
    return values


def _clean_env_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


def _config_value(name: str, file_values: dict[str, str]) -> str | None:
    if name in os.environ:
        return os.environ[name].strip() or None
    return file_values.get(name)


def _float_env(value: str | None, default: float) -> float:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
