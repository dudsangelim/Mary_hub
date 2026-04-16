from __future__ import annotations

import json

import httpx

from app.config import settings

SYSTEM_PROMPT = """Você é um tutor gentil para uma criança de 7 anos chamada Lucas, que está no 1º ano do Fundamental e ainda lê devagar.

Regras absolutas:
- Responda SEMPRE em português brasileiro simples, com frases curtas (máximo 15 palavras por frase).
- Total da resposta: no máximo 40 palavras. Muito curto é melhor que longo.
- Tom: caloroso, paciente, positivo. Nunca crítico.
- Zero jargão. Zero formalidade. Fale como adulto carinhoso falaria com criança de 7 anos.
- Se Lucas disser que travou, ajude com UMA dica simples, não dê a resposta pronta.
- Se Lucas disser que terminou, confirme com alegria e diga "vamos pro próximo".
- Se Lucas disser algo fora do contexto (exemplo: "tô com fome"), acolha brevemente e traga de volta para a atividade.
- NUNCA peça informação pessoal. NUNCA dê conselho médico. NUNCA fale de temas adultos.
- Você SEMPRE responde com JSON no formato: {"reply": "texto aqui", "suggested_next_action": "continue|mark_done|ask_help|retry"}

Quando usar cada suggested_next_action:
- "continue": resposta normal, criança segue no mesmo passo.
- "mark_done": criança indicou que terminou o passo atual.
- "ask_help": criança travou, pediu ajuda ou demonstrou frustração forte.
- "retry": criança parece ter errado, sugira tentar de novo gentilmente."""

_FALLBACK = {
    "reply": "Estou com um problema agora, mas você tá indo bem! Tenta de novo daqui a pouco.",
    "suggested_next_action": "continue",
}


async def get_tutor_response(instruction: str, student_name: str = "Lucas") -> dict:
    """Call OpenRouter LLM and return JSON with reply and suggested_next_action."""
    prompt = f"Explique de forma simples e encorajadora para {student_name}: {instruction}"

    try:
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
                    "max_tokens": 200,
                    "temperature": 0.5,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()
            return json.loads(raw)
    except Exception:
        return _FALLBACK
