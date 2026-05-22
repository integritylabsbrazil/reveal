#!/bin/bash

# ============================================================
# jira-create-tasks.sh
# Le status-tasks.json e cria subtasks no Jira interativamente.
#
# Uso: jira-create-tasks.sh TICKET_ID [--auto] [--clean] [--preview-only]
#
#   TICKET_ID    - Chave do ticket pai (ex: SPR-3413)
#   --auto       - Criar todas sem confirmacao individual
#   --clean      - Deletar subtasks antigas criadas pela ferramenta
#   --preview-only - Mostrar preview de todas sem criar
#
# Comportamento:
#   - Summary: [BACKEND] - descricao (ou [FRONTEND])
#   - Description: ADF com seções parseadas do texto de observacoes
#   - Para cada task: preview → confirmar → criar
#   - Opcoes: s (enviar), N (pular), e (editar), p (preview), q (sair)
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="JIRA-CREATE"
source "$SCRIPT_DIR/utils.sh"

AUTO=false
CLEAN=false
PREVIEW_ONLY=false
TICKET_ID=""

for arg in "$@"; do
    case "$arg" in
        --auto) AUTO=true ;;
        --clean) CLEAN=true ;;
        --preview-only) PREVIEW_ONLY=true ;;
        --help|-h)
            cat <<EOF
Uso: $0 TICKET_ID [--auto] [--clean] [--preview-only]

  TICKET_ID      - Chave do ticket pai (ex: SPR-3413)
  --auto         - Criar todas sem confirmacao individual
  --clean        - Deletar subtasks antigas criadas pela ferramenta
  --preview-only - Mostrar preview de todas sem criar

Fluxo interativo:
  s  - Enviar para o Jira
  N  - Pular esta task
  e  - Editar descricao antes de enviar (abre editor)
  p  - Mostrar preview novamente
  q  - Sair do processo
EOF
            exit 0
            ;;
        *) TICKET_ID="$arg" ;;
    esac
done

if [[ -z "$TICKET_ID" ]]; then
    echo "Uso: $0 TICKET_ID [--auto] [--clean] [--preview-only]"
    exit 1
fi

TICKET_DIR="$SCRIPT_DIR/../tickets/$TICKET_ID"

if [[ ! -f "$TICKET_DIR/status-tasks.json" ]]; then
    log_error "status-tasks.json nao encontrado em $TICKET_DIR"
    exit 1
fi

if ! source "$SCRIPT_DIR/jira-fetch.sh" 2>/dev/null; then :; fi
if ! load_credentials 2>/dev/null; then
    log_error "Credenciais Jira necessarias"
    echo "  Configure JIRA_USER + JIRA_TOKEN como env vars"
    echo "  Ou crie ~/.jira-credentials (formato: usuario:token)"
    exit 1
fi

# ============================================================
# Clean: deletar subtasks antigas criadas pela ferramenta
# ============================================================
if [[ "$CLEAN" == true ]]; then
    log_section "Clean: removendo subtasks antigas — $TICKET_ID"

    SUBTASKS=$(jira_api_get "/rest/api/${JIRA_API_VERSION:-3}/issue/${TICKET_ID}?fields=subtasks" 2>/dev/null | jq -c '.fields.subtasks // []') || {
        log_warn "Nao foi possivel buscar subtasks de $TICKET_ID"
        SUBTASKS="[]"
    }

    TOTAL=$(echo "$SUBTASKS" | jq 'length')
    echo "  Subtasks encontradas: $TOTAL"

    DELETED=0
    FAILED=0
    SKIPPED_CLEAN=0

    for row in $(echo "$SUBTASKS" | jq -r '.[] | @base64'); do
        _jq() { echo "$row" | base64 -d | jq -r "$1"; }
        KEY=$(_jq '.key')
        SUMMARY=$(_jq '.fields.summary')

        case "$SUMMARY" in
            \[BACKEND\]*|\[FRONTEND\]*|\[DUPLICATE\]*|\[TEST\]*)
                echo -n "  Removendo $KEY ($SUMMARY)... "
                if bash "$SCRIPT_DIR/jira-create-subtask.sh" --delete "$KEY" 2>/dev/null; then
                    echo "  OK"
                    DELETED=$((DELETED + 1))
                else
                    echo "  403 sem permissao"
                    FAILED=$((FAILED + 1))
                fi
                ;;
            *)
                SKIPPED_CLEAN=$((SKIPPED_CLEAN + 1))
                ;;
        esac
    done

    echo "  Resumo clean: $DELETED removidas, $FAILED falha (403), $SKIPPED_CLEAN mantidas"
    echo ""
fi

# ============================================================
# Helpers
# ============================================================

projeto_to_prefix() {
    local projeto="$1"
    case "$projeto" in
        *frontend*) echo "[FRONTEND]" ;;
        *)          echo "[BACKEND]"  ;;
    esac
}

resolve_task_refs() {
    local text="$1"
    local json_file="$2"
    while IFS="|" read -r task_id jira_key; do
        if [[ -n "$jira_key" ]]; then
            text="${text//task $task_id/$jira_key}"
            text="${text//Task $task_id/$jira_key}"
            text="${text//TASK $task_id/$jira_key}"
        fi
    done < <(jq -r '.tarefas[] | select(.jiraKey != null and .jiraKey != "") | "\(.id)|\(.jiraKey)"' "$json_file" 2>/dev/null)
    echo "$text"
}

# Preview do markdown bruto (stdout) para o usuario revisar
preview_description() {
    local observacoes="$1"
    echo ""
    echo "==================== PREVIEW DA DESCRICAO (MARKDOWN) ===================="
    echo ""
    echo "$observacoes"
    echo ""
    echo "========================================================================"
    echo ""
}

# Converte observacoes (markdown) para ADF JSON e imprime na stdout
# Uso: build_adf_description observacoes
build_adf_description() {
    local observacoes="$1"
    jq -n --arg observacoes "$observacoes" '{observacoes: $observacoes}' | \
    python3 "$SCRIPT_DIR/build_adf.py" 2>/dev/null || {
        log_warn "Falha ao gerar ADF, usando descricao simples"
        echo '{"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text":"ERRO AO GERAR ADF"}]}]}'
    }
}

# Editor temporario para descricao
edit_description() {
    local content="$1"
    local tmpfile
    tmpfile=$(mktemp)
    echo "$content" > "$tmpfile"

    local editor="${EDITOR:-nano}"
    if command -v "$editor" &>/dev/null; then
        $editor "$tmpfile" < /dev/tty > /dev/tty 2>&1 || true
    else
        for e in nano vim vi; do
            if command -v "$e" &>/dev/null; then
                $e "$tmpfile" < /dev/tty > /dev/tty 2>&1 || true
                break
            fi
        done
    fi

    cat "$tmpfile"
    rm -f "$tmpfile"
}

# ============================================================
# Main
# ============================================================

log_section "Criacao de Subtasks no Jira — $TICKET_ID"

PENDING_IDS=$(jq -c '[.tarefas[] | select((.jiraKey // "") == "") | .id]' "$TICKET_DIR/status-tasks.json" 2>/dev/null || echo "[]")
TOTAL_PENDING=$(echo "$PENDING_IDS" | jq 'length')

if [[ "$TOTAL_PENDING" -eq 0 ]]; then
    log_info "Todas as tasks ja possuem jiraKey. Nada a criar."
    exit 0
fi

echo "  Total de tasks sem jiraKey: $TOTAL_PENDING"
echo ""

CREATED=0
SKIPPED=0
FAILED=0

for task_id in $(echo "$PENDING_IDS" | jq -r '.[]'); do
    TASK_DATA=$(jq -c ".tarefas[] | select(.id == \"$task_id\")" "$TICKET_DIR/status-tasks.json")

    DESC=$(echo "$TASK_DATA" | jq -r '.descricao // "Sem descricao"')
    PROJETO=$(echo "$TASK_DATA" | jq -r '.projeto // "backend"')
    NIVEL=$(echo "$TASK_DATA" | jq -r '.nivel // "?"')
    TIPO=$(echo "$TASK_DATA" | jq -r '.tipo // "?"')
    HORAS=$(echo "$TASK_DATA" | jq -r '.esforcoEstimado.horas // "?"')
    DEPENDE=$(echo "$TASK_DATA" | jq -r '.dependeDe // [] | join(", ")')
    OBS=$(echo "$TASK_DATA" | jq -r '.observacoes // ""')
    OBS_TRUNC=$(echo "$OBS" | head -c 300)
    if [[ ${#OBS} -gt 300 ]]; then
        OBS_TRUNC="${OBS_TRUNC}..."
    fi

    PREFIX=$(projeto_to_prefix "$PROJETO")
    DEPENDE_TXT="${DEPENDE:-nenhuma}"
    OBS_RESOLVED=$(resolve_task_refs "$OBS" "$TICKET_DIR/status-tasks.json")
    DEPENDE_RESOLVED=$(resolve_task_refs "$DEPENDE_TXT" "$TICKET_DIR/status-tasks.json")

    echo "─────────────── Task $task_id/$TOTAL_PENDING ───────────────"
    echo "  ${PREFIX} - $DESC"
    echo "  Tipo: $TIPO | Esforco: ${HORAS}h | Depende: $DEPENDE_TXT"
    echo ""

    # Preview markdown
    preview_description "$OBS_RESOLVED"

    if [[ "$PREVIEW_ONLY" == true ]]; then
        echo "  (preview-only, task nao criada)"
        echo ""
        continue
    fi

    # Interactive confirmation
    while true; do
        if [[ "$AUTO" == true ]]; then
            REPLY="s"
        else
            echo "Opcoes: s=enviar  N=pular  e=editar  p=preview  q=sair"
            read -r -p "Acao: " REPLY
        fi

        case "$REPLY" in
            s|S|sim|SIM)
                echo ""
                log_info "Criando subtask no Jira..."

                SUMMARY="${PREFIX} - ${DESC}"
                DESCRIPTION_JSON=$(build_adf_description "$OBS_RESOLVED")

                CREATED_KEY=$(bash "$SCRIPT_DIR/jira-create-subtask.sh" "$TICKET_ID" "$SUMMARY" "$DESCRIPTION_JSON") || {
                    log_error "Falha ao criar subtask para task $task_id"
                    FAILED=$((FAILED + 1))
                    break
                }

                log_ok "Subtask $CREATED_KEY criada para task $task_id"

                jq --arg id "$task_id" --arg key "$CREATED_KEY" '
                    (.tarefas[] | select(.id == $id)).jiraKey = $key
                ' "$TICKET_DIR/status-tasks.json" > "${TICKET_DIR}/status-tasks.json.tmp" && \
                    mv "${TICKET_DIR}/status-tasks.json.tmp" "$TICKET_DIR/status-tasks.json"

                NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
                jq --arg now "$NOW" '.ultimaAtualizacao = $now' \
                    "$TICKET_DIR/status-tasks.json" > "${TICKET_DIR}/status-tasks.json.tmp" && \
                    mv "${TICKET_DIR}/status-tasks.json.tmp" "$TICKET_DIR/status-tasks.json"

                CREATED=$((CREATED + 1))
                echo ""
                break
                ;;
            e|E)
                echo ""
                log_info "Editando descricao..."
                NEW_OBS=$(edit_description "$OBS_RESOLVED")
                if [[ -n "$NEW_OBS" && "$NEW_OBS" != "$OBS_RESOLVED" ]]; then
                    OBS_RESOLVED="$NEW_OBS"
                    log_ok "Descricao atualizada. Novo preview:"
                    preview_description "$OBS_RESOLVED"
                else
                    log_info "Descricao nao alterada."
                fi
                ;;
            p|P)
                preview_description "$OBS_RESOLVED"
                ;;
            q|Q)
                log_info "Operacao cancelada pelo usuario."
                break 2
                ;;
            *)
                log_info "Task $task_id pulada."
                SKIPPED=$((SKIPPED + 1))
                break
                ;;
        esac
    done
done

echo ""
echo "─────────────── Resumo ───────────────"
echo "  Total processadas: $TOTAL_PENDING"
echo "  Criadas:           $CREATED"
echo "  Puladas:           $SKIPPED"
echo "  Falhas:            $FAILED"
echo "──────────────────────────────────────"
