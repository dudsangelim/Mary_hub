from __future__ import annotations

import hashlib

from app.config import settings
from app.redis import redis_client

TTS_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days
TTS_CACHE_PREFIX = "tts:audio:"


def _audio_key(text: str, voice: str, model: str) -> str:
    digest = hashlib.sha256(f"{model}:{voice}:{text}".encode()).hexdigest()
    return f"{TTS_CACHE_PREFIX}{digest}"


async def get_or_generate_tts(text: str, voice: str | None = None) -> tuple[bytes, bool]:
    """Returns (audio_bytes, was_cached)."""
    if not settings.openai_api_key:
        return b"", False

    resolved_voice = voice or settings.openai_tts_voice
    model = settings.openai_tts_model
    cache_key = _audio_key(text, resolved_voice, model)

    cached = await redis_client.get(cache_key)
    if cached is not None:
        return cached, True

    audio_bytes = await _call_openai_tts(text, resolved_voice, model)
    await redis_client.setex(cache_key, TTS_CACHE_TTL, audio_bytes)
    return audio_bytes, False


async def _call_openai_tts(text: str, voice: str, model: str) -> bytes:
    import httpx

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": text, "voice": voice},
        )
        response.raise_for_status()
        return response.content


def audio_cache_key(text: str, voice: str | None = None) -> str:
    resolved_voice = voice or settings.openai_tts_voice
    return _audio_key(text, resolved_voice, settings.openai_tts_model)
