#!/bin/bash

# ============================================================
# validate-ticket.sh
# Valida consistencia entre todos os documentos de um ticket.
# Uso: ./validate-ticket.sh TICKET_ID
# ============================================================

set -euo pipefail

TICKETS_DIR="./tickets"
HAS_ERROR=0

RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
NC='\033[0m'

usage() {
    cat <<EOF
Uso: $0 TICKET_ID

Valida consistencia entre os documentos do ticket:
  - status-tasks.json vs contexto-implementacao.md
  - status-tasks.json vs INDEX.md
  - implementation-plan.md (referencias arquivos)
  - description.md (desvios de CA)
  - roteiro-demo.md (alinhamento com estado real)

Opcoes:
  --all         Valida todos os tickets
  --help, -h    Exibir esta ajuda

Exemplos:
  $0 PROJ-123
  $0 --all
EOF
    exit 0
}

check() {
    local label="$1"
    local result="$2"
    if [[ "$result" == "OK" ]]; then
        echo -e "  ${GREEN}OK${NC} $label"
    else
        echo -e "  ${RED}FALHA${NC} $label"
        echo "    $result"
        HAS_ERROR=1
    fi
}

warn() {
    local label="$1"
    local msg="$2"
    echo -e "  ${YELLOW}AVISO${NC} $label"
    echo "    $msg"
}

validate_ticket() {
    local TICKET_ID="$1"
    local TICKET_DIR="$TICKETS_DIR/$TICKET_ID"

    echo ""
    echo "========================================"
    echo " Validando: $TICKET_ID"
    echo "========================================"

    if [[ ! -d "$TICKET_DIR" ]]; then
        echo -e "  ${RED}ERRO${NC} Diretorio nao encontrado: $TICKET_DIR"
        HAS_ERROR=1
        return
    fi

    # --- Verificacao 1: status-tasks.json x contexto-implementacao.md ---
    echo ""
    echo "--- 1. status-tasks.json vs contexto-implementacao.md ---"

    local TASKS_FILE="$TICKET_DIR/status-tasks.json"
    local CONTEXT_FILE="$TICKET_DIR/contexto-implementacao.md"

    if [[ -f "$TASKS_FILE" && -f "$CONTEXT_FILE" ]]; then
        if command -v jq &> /dev/null; then
            # Verificar se cada task no JSON tem entrada na tabela do MD
            while IFS=$'\t' read -r id status descricao; do
                if ! grep -q "| $id |" "$CONTEXT_FILE" 2>/dev/null; then
                    check "Task $id missing no contexto-implementacao.md" "Task $id ($descricao) nao encontrada na tabela do contexto"
                fi
            done < <(jq -r '.tarefas[] | [.id, .status, .descricao] | @tsv' "$TASKS_FILE")

            # Verificar status icons no MD
            while IFS=$'\t' read -r id status descricao; do
                expected_icon=""
                case "$status" in
                    concluido)   expected_icon="✅" ;;
                    cancelado)   expected_icon="❌" ;;
                    em_andamento) expected_icon="🔄" ;;
                    falhou)      expected_icon="💥" ;;
                    pendente)    expected_icon="⏳" ;;
                esac
                # Procurar a linha da task e verificar se tem o icone esperado
                line=$(grep "| $id |" "$CONTEXT_FILE" 2>/dev/null || true)
                if [[ -n "$line" ]]; then
                    if ! echo "$line" | grep -q "$expected_icon"; then
                        check "Task $id icon incorreto" "Esperado '$expected_icon' para status '$status', linha: $line"
                    fi
                fi
            done < <(jq -r '.tarefas[] | [.id, .status, .descricao] | @tsv' "$TASKS_FILE")

            # Verificar total
            json_total=$(jq '.tarefas | length' "$TASKS_FILE")
            json_concluidas=$(jq '[.tarefas[] | select(.status == "concluido")] | length' "$TASKS_FILE")
            json_canceladas=$(jq '[.tarefas[] | select(.status == "cancelado")] | length' "$TASKS_FILE")
            json_pendentes=$(jq '[.tarefas[] | select(.status == "pendente")] | length' "$TASKS_FILE")

            md_total_line=$(grep "^\\*\\*Total:" "$CONTEXT_FILE" 2>/dev/null || true)
            if echo "$md_total_line" | grep -q "Total:"; then
                # Extrair numeros - formato: "**Total:** N tarefas (X concluídas, Y canceladas, Z pendentes)"
                md_total=$(echo "$md_total_line" | sed -n 's/.*\*\*Total:\*\* \([0-9][0-9]*\).*/\1/p')
                md_concluidas=$(echo "$md_total_line" | sed -n 's/.*[^0-9]\([0-9][0-9]*\) concluídas.*/\1/p')
                md_canceladas=$(echo "$md_total_line" | sed -n 's/.*[^0-9]\([0-9][0-9]*\) canceladas.*/\1/p')

                if [[ "$md_total" != "$json_total" ]]; then
                    check "Total de tasks" "JSON: $json_total, MD: $md_total"
                fi
                if [[ "$md_concluidas" != "$json_concluidas" ]]; then
                    check "Total concluidas" "JSON: $json_concluidas, MD: $md_concluidas"
                fi
                if [[ "$md_canceladas" != "$json_canceladas" ]]; then
                    check "Total canceladas" "JSON: $json_canceladas, MD: $md_canceladas"
                fi
            fi

            check "Tasks sync" "OK"
        else
            warn "jq nao disponivel" "Instale jq para validacao automatica de status-tasks.json"
        fi
    else
        if [[ ! -f "$TASKS_FILE" ]]; then
            warn "status-tasks.json ausente" "Nao foi possivel validar tasks"
        fi
        if [[ ! -f "$CONTEXT_FILE" ]]; then
            warn "contexto-implementacao.md ausente" "Nao foi possivel validar contexto"
        fi
    fi

    # --- Verificacao 2: INDEX.md ---
    echo ""
    echo "--- 2. INDEX.md ---"

    local INDEX_FILE="$TICKETS_DIR/INDEX.md"
    if [[ -f "$INDEX_FILE" ]]; then
        index_line=$(grep "\[$TICKET_ID\]" "$INDEX_FILE" 2>/dev/null || true)
        if [[ -z "$index_line" ]]; then
            check "Ticket no INDEX.md" "Ticket $TICKET_ID nao encontrado no INDEX.md"
        elif [[ -f "$TASKS_FILE" ]] && command -v jq &> /dev/null; then
            total=$(jq '.tarefas | length' "$TASKS_FILE")
            # Verificar se o numero de tarefas no INDEX corresponde
            if echo "$index_line" | grep -q "$total tarefas"; then
                check "INDEX.md sync" "OK"
            else
                check "INDEX.md tasks count" "INDEX.md pode estar desatualizado para $TICKET_ID"
            fi
        else
            check "INDEX.md" "Ticket $TICKET_ID presente no INDEX"
        fi
    fi

    # --- Verificacao 3: implementation-plan.md ---
    echo ""
    echo "--- 3. implementation-plan.md (referencias) ---"

    local PLAN_FILE="$TICKET_DIR/implementation-plan.md"
    local plan_has_issues=0
    if [[ -f "$PLAN_FILE" ]]; then
        # Verificar se arquivos .java referenciados existem nos projetos
        while IFS='|' read -r _ _ arquivo _; do
            arquivo=$(echo "$arquivo" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            if [[ "$arquivo" =~ \.java$ ]] && [[ ! "$arquivo" =~ ^- ]]; then
                found=$(find "$TICKET_DIR/../../projetos" -name "$arquivo" 2>/dev/null | head -1)
                if [[ -z "$found" ]]; then
                    warn "Arquivo nao encontrado" "implementation-plan.md referencia '$arquivo' mas nao foi encontrado nos projetos"
                    plan_has_issues=1
                fi
            fi
        done < <(grep -E '^\|.*\.java' "$PLAN_FILE" 2>/dev/null || true)
        if [[ "$plan_has_issues" -eq 0 ]]; then
            check "implementation-plan.md" "OK"
        fi
    else
        warn "implementation-plan.md ausente" "Nao foi possivel validar"
    fi

    # --- Verificacao 4: description.md desvios ---
    echo ""
    echo "--- 4. description.md (desvios de CA) ---"

    local DESC_FILE="$TICKET_DIR/description.md"
    if [[ -f "$DESC_FILE" ]]; then
        # Verificar se ha secoes de desvio documentados
        if grep -qi "nao implementad" "$DESC_FILE" || grep -qi "desvio" "$DESC_FILE" || grep -qi "não foi" "$DESC_FILE"; then
            check "Desvios documentados" "OK"
        else
            # So dar warning se existirem tasks canceladas (pode indicar desvio nao documentado)
            if [[ -f "$TASKS_FILE" ]] && command -v jq &> /dev/null; then
                canceled=$(jq '[.tarefas[] | select(.status == "cancelado")] | length' "$TASKS_FILE")
                if [[ "$canceled" -gt 0 ]]; then
                    warn "Desvios podem nao estar documentados" "Ha $canceled tasks canceladas mas description.md pode nao documentar os desvios"
                fi
            fi
        fi
    fi

    # --- Verificacao 5: roteiro-demo.md ---
    echo ""
    echo "--- 5. roteiro-demo.md (alinhamento) ---"

    local DEMO_FILE="$TICKET_DIR/roteiro-demo.md"
    if [[ -f "$DEMO_FILE" ]]; then
        # Verificar se o roteiro menciona o estado real (nao-conectado ao BPMN etc.)
        if grep -qi "nao.*conectad" "$DEMO_FILE" || grep -qi "futur" "$DEMO_FILE" || grep -qi "estado atual" "$DEMO_FILE"; then
            check "roteiro-demo.md alinhado" "OK"
        else
            warn "roteiro-demo.md pode nao refletir estado real" "Nao foi encontrada indicacao de que features estao pendentes de conexao ao BPMN"
        fi
    fi

    # --- Verificacao 6: dependencias semanticas ---
    echo ""
    echo "--- 6. Dependencias semanticas ---"

    if [[ -f "$TASKS_FILE" ]] && command -v jq &> /dev/null; then
        # Verificar se tasks dependem de tasks canceladas
        while IFS=$'\t' read -r id dependes; do
            canceled_deps=""
            for dep in $(echo "$dependes" | tr ',' ' '); do
                dep_status=$(jq -r --arg d "$dep" '.tarefas[] | select(.id == $d) | .status' "$TASKS_FILE" 2>/dev/null || true)
                if [[ "$dep_status" == "cancelado" ]]; then
                    canceled_deps="$canceled_deps $dep"
                fi
            done
            if [[ -n "$canceled_deps" ]]; then
                warn "Task $id depende de task cancelada" "Dependencias canceladas:$canceled_deps — reavaliar necessidade"
            fi
        done < <(jq -r '.tarefas[] | select(.dependeDe | length > 0) | [.id, (.dependeDe | join(","))] | @tsv' "$TASKS_FILE")
        check "Dependencias semanticas" "OK"
    fi

    echo ""
    echo "--- Fim da validacao de $TICKET_ID ---"
}

# ============================================================
# Main
# ============================================================

if [[ $# -eq 0 ]]; then
    usage
fi

if [[ "$1" == "--all" ]]; then
    for ticket_dir in "$TICKETS_DIR"/[A-Z]*-[0-9]*/; do
        if [[ -d "$ticket_dir" ]]; then
            ticket_id=$(basename "$ticket_dir")
            validate_ticket "$ticket_id"
        fi
    done
else
    validate_ticket "$1"
fi

echo ""
if [[ "$HAS_ERROR" -eq 0 ]]; then
    echo -e "${GREEN}Todas as validacoes passaram.${NC}"
else
    echo -e "${RED}Algumas validacoes falharam. Reveja os itens marcados com FALHA.${NC}"
fi

exit "$HAS_ERROR"
