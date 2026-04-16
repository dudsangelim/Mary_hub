from __future__ import annotations

import httpx

from app.config import settings

SYSTEM_PROMPT = """Você é Mary, uma tutora virtual gentil e paciente para crianças do Ensino Fundamental.
Você está ajudando Lucas, um aluno do 1º ano. Use linguagem simples, clara e encorajadora.
Responda sempre em português. Seja breve e direto — no máximo 2-3 frases.
Nunca use linguagem técnica ou palavras difíceis. Use exemplos do cotidiano quando possível."""


async def get_tutor_response(instruction: str, student_name: str = "Lucas") -> str:
    """Call OpenRouter LLM and return the tutor's spoken text for this step."""
    prompt = f"Explique de forma simples e encorajadora para {student_name}: {instruction}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.tutor_lucas_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 150,
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
