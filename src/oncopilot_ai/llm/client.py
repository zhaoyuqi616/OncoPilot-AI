from __future__ import annotations

from openai import OpenAI

from oncopilot_ai.config import settings


def get_client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)
