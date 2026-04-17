#!/usr/bin/env bash
set -euo pipefail

API="http://localhost:8100/api/v1"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILURES=$((FAILURES+1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "      $1"; }

FAILURES=0

echo ""
echo "=========================================="
echo " Mary Hub v0.2.0 — Validação pós-deploy"
echo "=========================================="
echo ""

# --- 0. Infraestrutura ---
echo "--- 0. Infraestrutura ---"

if curl -sf "http://localhost:8100/health" > /dev/null 2>&1; then
  pass "Backend /health respondendo"
else
  fail "Backend /health NÃO responde"
  exit 1
fi

if docker compose exec -T postgres pg_isready -U mary -d mary_edu > /dev/null 2>&1; then
  pass "Postgres saudável"
else
  fail "Postgres não responde"
fi

if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
  pass "Redis saudável"
else
  fail "Redis não responde"
fi

echo ""

# --- 1. Auth ---
echo "--- 1. Autenticação ---"

TOKEN_RESPONSE=$(curl -sf -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"eduardo@mary.local","password":"mary2026"}' 2>/dev/null || echo "FAIL")

if echo "$TOKEN_RESPONSE" | jq -e '.tokens.access_token' > /dev/null 2>&1; then
  TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.tokens.access_token')
  pass "Login OK"
else
  fail "Login falhou. Rode: docker compose exec backend python -m app.seed"
  exit 1
fi

AUTH="Authorization: Bearer $TOKEN"

echo ""

# --- 2. Fase A — Seed e Schedule ---
echo "--- 2. Fase A — Seed e Schedule ---"

STUDENTS=$(curl -sf "$API/students" -H "$AUTH" 2>/dev/null)
STUDENT_COUNT=$(echo "$STUDENTS" | jq 'length' 2>/dev/null || echo "0")

if [ "$STUDENT_COUNT" -ge 2 ]; then
  pass "Estudantes cadastrados: $STUDENT_COUNT"
else
  fail "Esperava >= 2 estudantes, encontrou $STUDENT_COUNT"
fi

LUCAS_ID=$(echo "$STUDENTS" | jq -r '.[] | select(.name | test("Lucas")) | .id' 2>/dev/null | head -1)
MALU_ID=$(echo "$STUDENTS" | jq -r '.[] | select(.name == "Malu") | .id' 2>/dev/null | head -1)

[ -n "$LUCAS_ID" ] && pass "Lucas: $LUCAS_ID" || fail "Lucas NÃO encontrado"
[ -n "$MALU_ID" ] && pass "Malu: $MALU_ID" || fail "Malu NÃO encontrada"

# Lucas schedule
if [ -n "$LUCAS_ID" ]; then
  LUCAS_SCHED=$(curl -sf "$API/students/$LUCAS_ID/schedule" -H "$AUTH" 2>/dev/null || echo "{}")
  LUCAS_MON_BLOCKS=$(echo "$LUCAS_SCHED" | jq '.weekly_schedule.monday | length' 2>/dev/null || echo "0")
  LUCAS_FIRST_START=$(echo "$LUCAS_SCHED" | jq -r '.weekly_schedule.monday[0].start // empty' 2>/dev/null)
  LUCAS_SUN_WINDOWS=$(echo "$LUCAS_SCHED" | jq '.tutor_windows.sunday | length' 2>/dev/null || echo "0")

  [ "$LUCAS_MON_BLOCKS" -ge 5 ] && pass "Lucas: $LUCAS_MON_BLOCKS blocos segunda" || fail "Lucas: $LUCAS_MON_BLOCKS blocos segunda (esperava >= 5)"
  [ "$LUCAS_FIRST_START" = "13:15" ] && pass "Lucas: primeira aula 13:15 (tarde)" || fail "Lucas: primeira aula '$LUCAS_FIRST_START' (deveria ser 13:15)"
  [ "$LUCAS_SUN_WINDOWS" -ge 1 ] && pass "Lucas: janela domingo presente" || fail "Lucas: sem janela domingo"
fi

# Malu schedule
if [ -n "$MALU_ID" ]; then
  MALU_SCHED=$(curl -sf "$API/students/$MALU_ID/schedule" -H "$AUTH" 2>/dev/null || echo "{}")
  MALU_TUE_BLOCKS=$(echo "$MALU_SCHED" | jq '.weekly_schedule.tuesday | length' 2>/dev/null || echo "0")
  MALU_TUE_FIRST=$(echo "$MALU_SCHED" | jq -r '.weekly_schedule.tuesday[0].start // empty' 2>/dev/null)
  MALU_TUE_WINDOWS=$(echo "$MALU_SCHED" | jq '.tutor_windows.tuesday | length' 2>/dev/null || echo "0")
  MALU_WED_WINDOWS=$(echo "$MALU_SCHED" | jq '.tutor_windows.wednesday | length' 2>/dev/null || echo "0")
  MALU_ACTIVITIES=$(echo "$MALU_SCHED" | jq '.fixed_activities | length' 2>/dev/null || echo "0")

  [ "$MALU_TUE_BLOCKS" -ge 10 ] && pass "Malu: $MALU_TUE_BLOCKS blocos terça (integral)" || fail "Malu: $MALU_TUE_BLOCKS blocos terça (esperava >= 10)"
  [ "$MALU_TUE_FIRST" = "07:15" ] && pass "Malu: terça começa 07:15 (integral)" || fail "Malu: terça começa '$MALU_TUE_FIRST' (deveria ser 07:15)"
  [ "$MALU_TUE_WINDOWS" -eq 0 ] && pass "Malu: terça BLOQUEADA (0 janelas)" || fail "Malu: terça deveria ter 0 janelas, tem $MALU_TUE_WINDOWS"
  [ "$MALU_WED_WINDOWS" -ge 2 ] && pass "Malu: quarta com $MALU_WED_WINDOWS janelas (self_study + homework)" || fail "Malu: quarta deveria ter 2 janelas, tem $MALU_WED_WINDOWS"
  [ "$MALU_ACTIVITIES" -ge 1 ] && pass "Malu: fixed_activities presente (vôlei)" || fail "Malu: fixed_activities vazio"
fi

# Matérias 7º ano
SUBJECTS_7=$(docker compose exec -T postgres psql -U mary -d mary_edu -t -c \
  "SELECT count(*) FROM subjects WHERE grade='7_fund' AND is_active=true;" 2>/dev/null | tr -d ' ')
[ "$SUBJECTS_7" -ge 15 ] && pass "Matérias 7º ano: $SUBJECTS_7" || fail "Matérias 7º ano: $SUBJECTS_7 (esperava >= 15)"

echo ""

# --- 3. Fase B — Session Engine ---
echo "--- 3. Fase B — Session Engine ---"

if [ -n "$LUCAS_ID" ]; then
  STATUS=$(curl -sf "$API/tutor/status/$LUCAS_ID" -H "$AUTH" 2>/dev/null || echo "{}")
  AVAILABLE=$(echo "$STATUS" | jq -r '.available' 2>/dev/null)
  REASON=$(echo "$STATUS" | jq -r '.reason' 2>/dev/null)

  if [ "$AVAILABLE" = "true" ] || [ "$AVAILABLE" = "false" ]; then
    pass "GET /tutor/status → available=$AVAILABLE, reason='$REASON'"
  else
    fail "GET /tutor/status resposta inesperada"
  fi

  if [ "$AVAILABLE" = "true" ]; then
    info "Dentro da janela — testando sessão completa..."

    SESSION=$(curl -sf -X POST "$API/tutor/sessions" \
      -H "$AUTH" -H "Content-Type: application/json" \
      -d "{\"student_id\":\"$LUCAS_ID\",\"scheduled_date\":\"$(date +%Y-%m-%d)\"}" 2>/dev/null || echo "{}")
    SESSION_ID=$(echo "$SESSION" | jq -r '.id // empty' 2>/dev/null)
    STEP_COUNT=$(echo "$SESSION" | jq '.steps | length' 2>/dev/null || echo "0")

    [ -n "$SESSION_ID" ] && pass "POST /tutor/sessions → id=$SESSION_ID, steps=$STEP_COUNT" || fail "POST /tutor/sessions falhou"

    if [ -n "$SESSION_ID" ]; then
      # Next
      NEXT=$(curl -sf -X POST "$API/tutor/sessions/$SESSION_ID/next" \
        -H "$AUTH" -H "Content-Type: application/json" \
        -d '{"step_index": 0, "mark_done": false}' 2>/dev/null || echo "{}")
      NEXT_STEP=$(echo "$NEXT" | jq -r '.step.kind // empty' 2>/dev/null)
      [ -n "$NEXT_STEP" ] && pass "POST /next → step.kind=$NEXT_STEP" || warn "/next sem step (sessão pode estar vazia)"

      # Stuck
      STUCK_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$API/tutor/sessions/$SESSION_ID/stuck" \
        -H "$AUTH" -H "Content-Type: application/json" \
        -d '{"step_id": "test", "reason": "validacao"}' 2>/dev/null || echo "000")
      [ "$STUCK_CODE" = "200" ] && pass "POST /stuck → 200" || warn "POST /stuck → $STUCK_CODE"

      # Complete
      COMPL_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$API/tutor/sessions/$SESSION_ID/complete" \
        -H "$AUTH" -H "Content-Type: application/json" \
        -d '{"completion_notes": "teste validacao"}' 2>/dev/null || echo "000")
      [ "$COMPL_CODE" = "200" ] && pass "POST /complete → 200" || warn "POST /complete → $COMPL_CODE"
    fi
  else
    warn "Fora da janela — pulando testes de sessão ao vivo"
    info "Reason: $REASON"
    info "Teste manualmente dentro da janela do Lucas (20:15-21:30 BRT)"
  fi
fi

echo ""

# --- 4. Fase C — LLM + TTS ---
echo "--- 4. Fase C — LLM + TTS ---"

TTS_RESPONSE=$(curl -sf -X POST "$API/tutor/tts" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"text": "Olá Lucas, vamos estudar!"}' 2>/dev/null || echo "{}")
TTS_KEY=$(echo "$TTS_RESPONSE" | jq -r '.audio_key // empty' 2>/dev/null)

if [ -n "$TTS_KEY" ] && [ "$TTS_KEY" != "null" ]; then
  pass "POST /tutor/tts → audio_key presente"

  HTTP_CODE=$(curl -sf -o /tmp/mary_test.mp3 -w "%{http_code}" "$API/tutor/tts/$TTS_KEY" -H "$AUTH" 2>/dev/null || echo "000")
  FILE_SIZE=$(wc -c < /tmp/mary_test.mp3 2>/dev/null || echo "0")

  if [ "$HTTP_CODE" = "200" ] && [ "$FILE_SIZE" -gt 100 ]; then
    pass "GET /tutor/tts/{key} → mp3 válido ($FILE_SIZE bytes)"
  else
    warn "TTS retornou $HTTP_CODE ($FILE_SIZE bytes). OPENAI_API_KEY configurada?"
  fi
  rm -f /tmp/mary_test.mp3
else
  warn "TTS sem audio_key. OPENAI_API_KEY pode estar vazio (OK pra teste sem áudio)"
fi

if [ -n "${SESSION_ID:-}" ]; then
  MSG=$(curl -sf -X POST "$API/tutor/sessions/$SESSION_ID/message" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d '{"user_message": "oi, tô pronto!", "step_id": null}' 2>/dev/null || echo "{}")
  REPLY=$(echo "$MSG" | jq -r '.reply_text // empty' 2>/dev/null)
  [ -n "$REPLY" ] && pass "POST /message → '${REPLY:0:50}...'" || fail "POST /message sem reply. OPENROUTER_API_KEY configurada?"
else
  warn "Sem sessão ativa — pulando teste /message"
fi

echo ""

# --- 5. Fase D — Frontend ---
echo "--- 5. Fase D — Frontend ---"

FRONT_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:3100" 2>/dev/null || echo "000")
[ "$FRONT_CODE" = "200" ] && pass "Frontend :3100 → 200" || fail "Frontend → $FRONT_CODE"

MANIFEST_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:3100/manifest.json" 2>/dev/null || echo "000")
[ "$MANIFEST_CODE" = "200" ] && pass "manifest.json acessível" || fail "manifest.json → $MANIFEST_CODE"

SW_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:3100/sw.js" 2>/dev/null || echo "000")
[ "$SW_CODE" = "200" ] && pass "sw.js acessível" || warn "sw.js → $SW_CODE"

if [ -n "$LUCAS_ID" ]; then
  TUTOR_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:3100/tutor/$LUCAS_ID" 2>/dev/null || echo "000")
  [ "$TUTOR_CODE" = "200" ] && pass "/tutor/$LUCAS_ID carrega" || fail "/tutor/$LUCAS_ID → $TUTOR_CODE"
fi

echo ""

# --- 6. Regressão v0.1 ---
echo "--- 6. Regressão — Endpoints v0.1 ---"

for EP in "students" "tasks" "materials" "dashboard/today" "dashboard/summary"; do
  CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$API/$EP" -H "$AUTH" 2>/dev/null || echo "000")
  [ "$CODE" = "200" ] && pass "GET /$EP → 200" || fail "GET /$EP → $CODE"
done

echo ""

# --- Resumo ---
echo "=========================================="
if [ "$FAILURES" -eq 0 ]; then
  echo -e "${GREEN} TODAS AS VALIDAÇÕES PASSARAM ${NC}"
  echo ""
  echo "Próximos passos:"
  echo "  1. Abrir http://<vps-ip>:3100/tutor/$LUCAS_ID no tablet"
  echo "  2. Testar dentro da janela do Lucas (20:15-21:30 BRT)"
  echo "  3. Se TTS não tocar: tablet pode exigir HTTPS pra autoplay"
else
  echo -e "${RED} $FAILURES FALHA(S) ENCONTRADA(S) ${NC}"
fi
echo "=========================================="

exit $FAILURES
