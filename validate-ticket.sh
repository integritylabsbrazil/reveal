#!/bin/bash

# ============================================================
# validate-ticket.sh
# Valida consistencia entre todos os documentos de um ticket.
# Uso: ./validate-ticket.sh TICKET_ID
# ============================================================

set -euo pipefail

TICKETS_DIR="./tickets"
HAS_ERROR=0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_PREFIX="VALIDATE"
source "$SCRIPT_DIR/lib/utils.sh"

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

check_warn() {
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
            check_warn "jq nao disponivel" "Instale jq para validacao automatica de status-tasks.json"
        fi
    else
        if [[ ! -f "$TASKS_FILE" ]]; then
            check_warn "status-tasks.json ausente" "Nao foi possivel validar tasks"
        fi
        if [[ ! -f "$CONTEXT_FILE" ]]; then
            check_warn "contexto-implementacao.md ausente" "Nao foi possivel validar contexto"
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
                # Tenta ler caminho do projeto do status-tasks.json
                PROJ_PATH=$(jq -r '.tarefas[0].caminhoProjeto // ""' "$TASKS_FILE" 2>/dev/null)
                if [[ -z "$PROJ_PATH" || "$PROJ_PATH" == "null" ]]; then
                    PROJ_PATH="$TICKET_DIR/../.."
                fi
                found=$(find "$PROJ_PATH" -name "$arquivo" 2>/dev/null | head -1)
                if [[ -z "$found" ]]; then
                    check_warn "Arquivo nao encontrado" "implementation-plan.md referencia '$arquivo' mas nao foi encontrado nos projetos"
                    plan_has_issues=1
                fi
            fi
        done < <(grep -E '^\|.*\.java' "$PLAN_FILE" 2>/dev/null || true)
        if [[ "$plan_has_issues" -eq 0 ]]; then
            check "implementation-plan.md" "OK"
        fi
    else
        check_warn "implementation-plan.md ausente" "Nao foi possivel validar"
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
                    check_warn "Desvios podem nao estar documentados" "Ha $canceled tasks canceladas mas description.md pode nao documentar os desvios"
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
            check_warn "roteiro-demo.md pode nao refletir estado real" "Nao foi encontrada indicacao de que features estao pendentes de conexao ao BPMN"
        fi
    fi

    # --- Verificacao 7: schema JSON ---
    echo ""
    echo "--- 7. Schema JSON ---"

    if command -v python3 &> /dev/null; then
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        for json_file in "$TICKET_DIR"/status-tasks.json "$TICKET_DIR"/impact-report.json "$TICKET_DIR"/jira-data.json; do
            if [[ -f "$json_file" ]]; then
                filename=$(basename "$json_file")
                case "$filename" in
                    status-tasks.json) schema="status_tasks" ;;
                    impact-report.json) schema="impact_report" ;;
                    jira-data.json) schema="jira_data" ;;
                esac
                errors=$(python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/lib')
from utils import validate_file
errs = validate_file('$json_file', '$schema')
for e in errs:
    print(e)
" 2>/dev/null)
                if [[ -n "$errors" ]]; then
                    while IFS= read -r line; do
                        check "Schema: $filename" "$line"
                    done <<< "$errors"
                fi
            fi
        done
        check "Schema JSON" "OK"
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
                check_warn "Task $id depende de task cancelada" "Dependencias canceladas:$canceled_deps — reavaliar necessidade"
            fi
        done < <(jq -r '.tarefas[] | select(.dependeDe | length > 0) | [.id, (.dependeDe | join(","))] | @tsv' "$TASKS_FILE")
        check "Dependencias semanticas" "OK"
    fi

    # --- Verificacao 8: Refinamento tecnico sections ---
    echo ""
    echo "--- 8. Refinamento tecnico (sections completude) ---"

    local REF_FILE="$TICKET_DIR/refinamento-tecnico.md"
    if [[ -f "$REF_FILE" ]]; then
        local missing_sections=()
        local section_patterns=(
            "Dados do Ticket"
            "Objetivo Funcional"
            "Contexto de Neg"
            "Impacto T"
            "Fluxo T"
            "Decis"
            "Riscos T"
            "Perguntas para o Neg"
            "Configura"
            "Depend"
            "Seguran"
            "Observa"
            "Tasks"
            "Checklist de Implementa"
            "Matriz de Rastreabilidade"
        )
        for pattern in "${section_patterns[@]}"; do
            if ! grep -qi "$pattern" "$REF_FILE" 2>/dev/null; then
                missing_sections+=("$pattern")
            fi
        done
        if [[ ${#missing_sections[@]} -eq 0 ]]; then
            check "Refinamento sections" "OK"
        else
            check "Refinamento sections" "Sections faltando: ${missing_sections[*]}"
        fi

        # Verificar se a matriz de rastreabilidade tem conteudo
        if grep -q "Matriz de Rastreabilidade" "$REF_FILE" 2>/dev/null; then
            local matrix_line_count
            matrix_line_count=$(sed -n '/## 15. Matriz/,/^---/p' "$REF_FILE" 2>/dev/null | grep -c '| [0-9]' || true)
            if [[ "$matrix_line_count" -gt 0 ]]; then
                check "Matriz rastreabilidade ($matrix_line_count entradas)" "OK"
            else
                check_warn "Matriz rastreabilidade vazia" "Matriz de rastreabilidade existe mas sem entradas automaticas"
            fi
        fi

        # Verificar se observacoes tecnicas tem conteudo por task
        if grep -q "## 12. Observa" "$REF_FILE" 2>/dev/null; then
            local obs_lines
            obs_lines=$(sed -n '/## 12. Observa/,/^---/p' "$REF_FILE" 2>/dev/null | grep -c '| [0-9]' || echo 0)
            if [[ "$obs_lines" -gt 0 ]]; then
                check "Observacoes tecnicas ($obs_lines tasks)" "OK"
            else
                check_warn "Observacoes tecnicas ausentes" "Secao de observacoes tecnicas existe mas sem entradas por task"
            fi
        fi
    else
        check_warn "refinamento-tecnico.md ausente" "Nao foi possivel validar sections"
    fi

    # --- Verificacao 9: Qualidade das observacoes tecnicas por task ---
    echo ""
    echo "--- 9. Observacoes tecnicas (qualidade) ---"

    if [[ -f "$TASKS_FILE" ]] && command -v jq &> /dev/null; then
        local low_quality_tasks=0
        while IFS=$'\t' read -r id descricao nivel observacoes; do
            local obs_len=${#observacoes}
            # Verificar se observacao tem conteudo minimo (100+ chars)
            if [[ "$obs_len" -lt 100 ]]; then
                # Mas ignorar tasks de demo/testes que tem observacoes naturais curtas
                if echo "$descricao" | grep -qi "demo\|teste\|artifact\|postman"; then
                    true  # ok, tasks de demo podem ter observacoes curtas
                else
                    check_warn "Task $id observacoes curtas" "Apenas $obs_len caracteres (task: $nivel, $descricao)"
                    low_quality_tasks=$((low_quality_tasks + 1))
                fi
            fi
            # Verificar se referencia classes do projeto
            if [[ "$nivel" == "senior" || "$nivel" == "pleno" ]]; then
                if [[ ! "$observacoes" =~ [A-Z][a-zA-Z]+\.(java|class) ]] && \
                   [[ ! "$observacoes" =~ [a-z]+\.[a-z]+\.[a-zA-Z]+ ]]; then
                    check_warn "Task $id sem referencia a classes" "Task senior/pleno sem referencia a classes/pacotes existentes"
                fi
            fi
        done < <(jq -r '.tarefas[] | [.id, .descricao, .nivel, (.observacoes // "")] | @tsv' "$TASKS_FILE" 2>/dev/null)
        if [[ "$low_quality_tasks" -eq 0 ]]; then
            check "Observacoes tecnicas qualidade" "OK"
        fi
    fi

    # --- Verificacao 10: Projeto tasks vs projetos-context ---
    echo ""
    echo "--- 10. Tasks referenciam projetos validos ---"

    if [[ -f "$TASKS_FILE" ]] && command -v jq &> /dev/null; then
        local context_dir="$SCRIPT_DIR/projects-context"
        if [[ -d "$context_dir" ]]; then
            while IFS=$'\t' read -r id projeto caminho; do
                # Verificar se existe context file para este projeto
                local context_file="$context_dir/${projeto}.md"
                if [[ ! -f "$context_file" ]]; then
                    check_warn "Task $id projeto sem context" "Projeto '$projeto' nao tem arquivo em projects-context/"
                fi
                # Verificar se o caminho do projeto existe
                if [[ -n "$caminho" && "$caminho" != "null" ]]; then
                    local abs_path
                    abs_path=$(realpath "$SCRIPT_DIR/$caminho" 2>/dev/null || echo "")
                    if [[ -z "$abs_path" || ! -d "$abs_path" ]]; then
                        check_warn "Task $id caminho invalido" "Caminho '$caminho' nao existe ou eh invalido"
                    fi
                fi
            done < <(jq -r '.tarefas[] | [.id, (.projeto // ""), (.caminhoProjeto // "")] | @tsv' "$TASKS_FILE" 2>/dev/null)
            check "Projetos validos" "OK"
        else
            check_warn "projects-context/ nao encontrado" "Nao foi possivel validar projetos"
        fi
    fi

    # --- Verificacao 11: Score de Qualidade do Refinamento ---
    echo ""
    echo "--- 11. Score de Qualidade do Refinamento ---"

    local score=0
    local max_score=10
    local details=()

    if [[ -f "$REF_FILE" ]]; then
        # Criterio 1: Sections obrigatorias (2 pontos)
        local req_patterns=("Dados do Ticket" "Objetivo Funcional" "Impacto T" "Observa" "Tasks" "Checklist" "Matriz de Rastreabilidade")
        local found_sections=0
        for p in "${req_patterns[@]}"; do
            if grep -qi "$p" "$REF_FILE" 2>/dev/null; then
                found_sections=$((found_sections + 1))
            fi
        done
        if [[ "$found_sections" -ge 6 ]]; then
            score=$((score + 2))
            details+=("Sections: 2/2")
        elif [[ "$found_sections" -ge 4 ]]; then
            score=$((score + 1))
            details+=("Sections: 1/2")
        fi

        # Criterio 2: Matriz de rastreabilidade preenchida (2 pontos)
        if [[ -f "$TASKS_FILE" ]] && command -v jq &>/dev/null; then
            local matrix_count
            matrix_count=$(sed -n '/Matriz de Rastreabilidade/,/^---/p' "$REF_FILE" 2>/dev/null | grep -cP '^\| *[0-9]' || true)
            if [[ "$matrix_count" -ge 3 ]]; then
                score=$((score + 2))
                details+=("Matriz rastreab.: 2/2")
            elif [[ "$matrix_count" -ge 1 ]]; then
                score=$((score + 1))
                details+=("Matriz rastreab.: 1/2")
            fi
        fi

        # Criterio 3: Observacoes tecnicas por task (2 pontos)
        local obs_count
        obs_count=$(sed -n '/## 12\. Observa/,/^---/p' "$REF_FILE" 2>/dev/null | grep -cP '^\| *[0-9]' || echo 0)
        if [[ "$obs_count" -ge 3 ]]; then
            score=$((score + 2))
            details+=("Observ. tecnicas: 2/2")
        elif [[ "$obs_count" -ge 1 ]]; then
            score=$((score + 1))
            details+=("Observ. tecnicas: 1/2")
        fi
    fi

    if [[ -f "$TASKS_FILE" ]] && command -v jq &>/dev/null; then
        # Criterio 4: Observacoes enriquecidas (2 pontos)
        local enriched_count=0
        local total_tasks
        total_tasks=$(jq '.tarefas | length' "$TASKS_FILE")
        while IFS= read -r obs; do
            if echo "$obs" | grep -qi "contexto do projeto\|projects-context\|Controllers de referencia\|Services de referencia"; then
                enriched_count=$((enriched_count + 1))
            fi
        done < <(jq -r '.tarefas[] | .observacoes // ""' "$TASKS_FILE" 2>/dev/null)
        if [[ "$total_tasks" -gt 0 ]] && [[ "$enriched_count" -eq "$total_tasks" ]]; then
            score=$((score + 2))
            details+=("Observ. enriquec.: 2/2")
        elif [[ "$enriched_count" -gt 0 ]]; then
            score=$((score + 1))
            details+=("Observ. enriquec.: 1/2")
        fi

        # Criterio 5: Esforco estimado presente (2 pontos)
        local effort_count
        effort_count=$(jq '[.tarefas[] | select(.esforcoEstimado != null)] | length' "$TASKS_FILE" 2>/dev/null || echo 0)
        if [[ "$effort_count" -eq "$total_tasks" ]]; then
            score=$((score + 2))
            details+=("Esforco estimado: 2/2")
        elif [[ "$effort_count" -gt 0 ]]; then
            score=$((score + 1))
            details+=("Esforco estimado: 1/2")
        fi
    fi

    # Exibir score
    local stars=""
    if [[ "$score" -ge 9 ]]; then stars="★★★★★"
    elif [[ "$score" -ge 7 ]]; then stars="★★★★☆"
    elif [[ "$score" -ge 5 ]]; then stars="★★★☆☆"
    elif [[ "$score" -ge 3 ]]; then stars="★★☆☆☆"
    else stars="★☆☆☆☆"
    fi

    echo ""
    echo "  Score: $score/$max_score $stars"
    for d in "${details[@]}"; do
        echo "    - $d"
    done

    if [[ "$score" -ge 7 ]]; then
        check "Qualidade do refinamento (score $score/$max_score)" "OK"
    elif [[ "$score" -ge 4 ]]; then
        check_warn "Qualidade do refinamento" "Score $score/$max_score — pode ser melhorado"
    else
        check "Qualidade do refinamento" "Score baixo ($score/$max_score) — refinamento precisa de revisao"
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
