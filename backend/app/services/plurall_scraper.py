"""
plurall_scraper.py — Scraper real do portal Plurall via serviço local de scraping.

Usa o scraping_service (Playwright) rodando em http://127.0.0.1:3002
para autenticar e extrair dados do aluno no portal plurall.net.

Interface pública:
    run_plurall_sync(credentials: dict) -> PlurallSnapshot
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

log = logging.getLogger(__name__)

SCRAPING_SERVICE_URL = os.environ.get("SCRAPING_SERVICE_URL", "http://127.0.0.1:3002")
PLURALL_BASE_URL = "https://www.plurall.net"
PLURALL_LOGIN_URL = f"{PLURALL_BASE_URL}/login"

# Timeout total para o scraping completo (segundos)
SCRAPE_TOTAL_TIMEOUT_S = 40
# Timeout que enviamos ao Playwright por operação (ms)
SCRAPE_OP_TIMEOUT_MS = 20_000
# Timeout httpx para falar com o serviço de scraping
HTTPX_TIMEOUT_S = 45


@dataclass
class PlurallSnapshot:
    """Dados extraídos do portal Plurall após autenticação."""

    success: bool
    student_name: str = ""
    student_role: str = "Aluno"
    school_name: str = ""
    class_name: str = ""
    grade: str = ""
    grade_label: str = ""
    modules_discovered: list[str] = field(default_factory=list)
    supports_assignments: bool = False
    supports_books: bool = False
    supports_assessments: bool = True
    supports_results: bool = True
    error: str = ""
    raw_text: str = ""


async def _scrape(
    url: str,
    actions: list[dict] | None = None,
    wait_for: str | None = None,
) -> dict[str, Any]:
    """Call local scraping service."""
    payload: dict[str, Any] = {
        "url": url,
        "formats": ["markdown", "html"],
        "timeout": SCRAPE_OP_TIMEOUT_MS,
    }
    if actions:
        payload["actions"] = actions
    if wait_for:
        payload["waitFor"] = wait_for

    async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT_S) as client:
        response = await client.post(f"{SCRAPING_SERVICE_URL}/v1/scrape", json=payload)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise RuntimeError(f"Scraping service returned failure: {data}")
        return data["data"]


def _extract_student_info(markdown: str, html: str) -> dict[str, str]:
    """Extract student info from page content using heuristics."""
    info: dict[str, str] = {}
    combined = html + "\n" + markdown

    # Student name patterns
    name_patterns = [
        r"Olá,\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)+)",
        r"Bem-vindo[oa],\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)+)",
        r'"name"\s*:\s*"([^"]{5,60})"',
        r'"displayName"\s*:\s*"([^"]{5,60})"',
        r'"student_name"\s*:\s*"([^"]{5,60})"',
        r'"fullName"\s*:\s*"([^"]{5,60})"',
    ]
    for pattern in name_patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            info["student_name"] = match.group(1).strip()
            break

    # School name
    for pattern in [
        r'"school(?:Name|_name)"\s*:\s*"([^"]+)"',
        r"Escola:\s*([^\n<]{5,80})",
        r"Colégio:\s*([^\n<]{5,80})",
    ]:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            info["school_name"] = match.group(1).strip()
            break

    # Class/grade
    for pattern in [
        r'"class(?:Name|_name|Label)"\s*:\s*"([^"]+)"',
        r'"grade(?:Name|Label|_label)"\s*:\s*"([^"]+)"',
        r"(\d+[oaº]\s+[Aa]no\s+(?:do\s+)?[Ee]nsino\s+[Ff]undamental)",
        r"(\d+[oaº]\s+[Aa]no\s+(?:do\s+)?[Ee]nsino\s+[Mm]édio)",
    ]:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            info["class_name"] = match.group(1).strip()
            break

    # Navigation modules
    module_keywords = [
        "Biblioteca de Conteúdos",
        "Biblioteca",
        "Simulados",
        "Provas",
        "Tarefas",
        "Atividades",
        "Maestro",
        "Resultados",
        "Assistente Inteligente",
        "Material Didático",
    ]
    modules_found = [m for m in module_keywords if m.lower() in combined.lower()]
    if modules_found:
        info["modules"] = ",".join(modules_found)

    return info


def _classify_grade(class_name: str) -> tuple[str, str]:
    """Convert '1º Ano Ensino Fundamental' → ('1_fund', '1º ano do Ensino Fundamental')."""
    if not class_name:
        return ("unknown", class_name or "Desconhecido")
    text = class_name.lower()
    match = re.search(r"(\d+)[oaº°]?\s*ano.*fundamental", text)
    if match:
        n = match.group(1)
        return (f"{n}_fund", f"{n}º ano do Ensino Fundamental")
    match = re.search(r"(\d+)[oaº°]?\s*ano.*médio", text)
    if match:
        n = match.group(1)
        return (f"{n}_medio", f"{n}º ano do Ensino Médio")
    if "pré" in text or "infantil" in text:
        return ("ei", "Educação Infantil")
    return ("unknown", class_name)


async def _do_scrape(username: str, password: str) -> PlurallSnapshot:
    """Core scraping logic — called with asyncio.timeout wrapper."""
    log.info("Carregando página de login do Plurall...")
    login_result = await _scrape(
        url=PLURALL_LOGIN_URL,
        actions=[
            # Wait for any input to appear before trying to fill
            {"type": "wait_for_selector", "selector": "input"},
            # Try to fill email field (multiple selector variants)
            {"type": "fill", "selector": "input[type='email']", "value": username},
            {"type": "fill", "selector": "input[type='password']", "value": password},
            # Click the submit button
            {"type": "click", "selector": "button[type='submit']"},
            # Wait 3s for navigation
            {"type": "wait", "milliseconds": 3000},
        ],
        # Don't block on this selector — just try and continue
        wait_for=None,
    )

    markdown = login_result.get("markdown", "") or ""
    html = login_result.get("html", "") or ""
    final_url = login_result.get("url", "")

    log.info("Resposta do Plurall, URL final: %s", final_url)

    # If still on login page, credentials may be wrong
    if "/login" in final_url and "dashboard" not in final_url and "home" not in final_url:
        error_indicators = ["senha incorreta", "usuário não encontrado", "invalid credentials", "erro ao fazer login", "incorrect"]
        detected = next((i for i in error_indicators if i in (markdown + html).lower()), None)
        if detected:
            return PlurallSnapshot(
                success=False,
                error=f"Login no Plurall falhou: '{detected}' detectado na página.",
            )
        # Could still be loading — extract what we can anyway
        log.info("URL ainda tem /login mas sem mensagem de erro, continuando extração...")

    info = _extract_student_info(markdown, html)
    student_name = info.get("student_name", "")
    school_name = info.get("school_name", "")
    class_name = info.get("class_name", "")
    modules_raw = info.get("modules", "")
    modules = [m.strip() for m in modules_raw.split(",") if m.strip()] if modules_raw else []

    grade_slug, grade_label = _classify_grade(class_name)

    modules_lower = [m.lower() for m in modules]
    supports_assignments = any("tarefa" in m or "atividade" in m for m in modules_lower)
    supports_books = any("biblioteca" in m or "livro" in m or "material" in m for m in modules_lower)
    supports_assessments = any("simulado" in m or "prova" in m for m in modules_lower)
    supports_results = any("resultado" in m for m in modules_lower)

    log.info(
        "Extração concluída: aluno=%s escola=%s turma=%s módulos=%d",
        student_name or "(não detectado)",
        school_name or "(não detectado)",
        class_name or "(não detectado)",
        len(modules),
    )

    return PlurallSnapshot(
        success=True,
        student_name=student_name or "Aluno Plurall",
        student_role="Aluno",
        school_name=school_name or "Escola",
        class_name=class_name or "",
        grade=grade_slug,
        grade_label=grade_label,
        modules_discovered=modules,
        supports_assignments=supports_assignments,
        supports_books=supports_books,
        supports_assessments=supports_assessments,
        supports_results=supports_results,
        raw_text=markdown[:2000],
    )


async def run_plurall_sync(credentials: dict) -> PlurallSnapshot:
    """
    Autentica no Plurall e extrai dados do aluno.

    Tem timeout total de SCRAPE_TOTAL_TIMEOUT_S segundos.
    Se exceder ou falhar, retorna PlurallSnapshot(success=False).
    """
    username = credentials.get("username", "")
    password = credentials.get("password", "")

    if not username or not password:
        return PlurallSnapshot(success=False, error="Credenciais incompletas (username/password obrigatórios)")

    # Quick health check on scraping service
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            health = await client.get(f"{SCRAPING_SERVICE_URL}/health")
            if health.status_code != 200:
                raise RuntimeError("status não-200")
    except Exception as exc:
        log.warning("Serviço de scraping indisponível: %s", exc)
        return PlurallSnapshot(success=False, error=f"Serviço de scraping indisponível: {exc}")

    log.info("Iniciando sync Plurall (timeout=%ds) para %s...", SCRAPE_TOTAL_TIMEOUT_S, username[:3] + "***")

    try:
        async with asyncio.timeout(SCRAPE_TOTAL_TIMEOUT_S):
            return await _do_scrape(username, password)
    except TimeoutError:
        log.warning("Sync Plurall excedeu %ds — usando fallback", SCRAPE_TOTAL_TIMEOUT_S)
        return PlurallSnapshot(
            success=False,
            error=(
                f"Timeout: o portal Plurall demorou mais de {SCRAPE_TOTAL_TIMEOUT_S}s para responder. "
                "Usando snapshot local. Tente novamente mais tarde ou verifique o acesso ao plurall.net."
            ),
        )
    except Exception as exc:
        log.exception("Erro inesperado no sync Plurall")
        return PlurallSnapshot(success=False, error=f"Erro inesperado: {exc}")


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import dataclasses
    import json
    import sys

    if len(sys.argv) < 3:
        print("Uso: python3 plurall_scraper.py <username> <password>")
        sys.exit(1)

    result = asyncio.run(run_plurall_sync({"username": sys.argv[1], "password": sys.argv[2]}))
    print(json.dumps(dataclasses.asdict(result), ensure_ascii=False, indent=2))
