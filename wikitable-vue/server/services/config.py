from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_MODEL = "gpt-5.5"
DEFAULT_BASE_URL = "https://newapi.lxhei.xyz/v1"


@dataclass(frozen=True)
class LLMConfig:
    model: str
    base_url: str
    api_key: str | None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


def get_llm_config() -> LLMConfig:
    return LLMConfig(
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
