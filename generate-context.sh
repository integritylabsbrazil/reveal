#!/bin/bash

# ============================================================
# generate-context.sh
# Gera contexto-implementacao.md a partir de status-tasks.json.
# Uso: ./generate-context.sh TICKET_ID
# ============================================================

set -euo pipefail

TICKETS_DIR="./tickets"

usage() {
    cat <<EOF
Uso: $0 TICKET_ID

Gera/atualiza contexto-implementacao.md a partir de status-tasks.json.

Mantem a seção de Observações se ja existir (append-only).
Reescreve a tabela de subtarefas, total, dependencias e projetos.

Exemplos:
  $0 PROJ-123
  $0 PROJ-456
EOF
    exit 0
}

if [[ $# -ne 1 || "$1" == "--help" || "$1" == "-h" ]]; then
    usage
fi

TICKET_ID="$1"
TICKET_DIR="$TICKETS_DIR/$TICKET_ID"
TASKS_FILE="$TICKET_DIR/status-tasks.json"
CONTEXT_FILE="$TICKET_DIR/contexto-implementacao.md"

if [[ ! -f "$TASKS_FILE" ]]; then
    echo "Erro: $TASKS_FILE nao encontrado" >&2
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Erro: jq necessario. Instale com: sudo apt-get install jq" >&2
    exit 1
fi

# Extrair observacoes existentes (se o arquivo ja existir)
OBSERVACOES=""
if [[ -f "$CONTEXT_FILE" ]]; then
    OBSERVACOES=$(sed -n '/^## Observacoes/,$p' "$CONTEXT_FILE" 2>/dev/null | tail -n +2 || true)
fi

# Gerar novo conteudo
exec 3>&1
{
    echo "# Contexto de Implementação — $TICKET_ID"
    echo ""

    # Resumo
    SUMMARY=$(jq -r '.ticketId' "$TASKS_FILE")
    echo "## $SUMMARY"
    echo ""

    # Tabela de subtarefas
    echo "## Subtarefas"
    echo ""
    echo "| # | Projeto | Descrição | Status | Tipo |"
    echo "|---|---------|-----------|--------|------|"

    jq -r '.tarefas[] | [
        .id,
        (.projeto | split("/")[-1]),
        .descricao,
        .status,
        .tipo
    ] | @tsv' "$TASKS_FILE" | while IFS=$'\t' read -r id projeto descricao status tipo; do
        case "$status" in
            concluido)   ic="✅" ;;
            cancelado)   ic="❌" ;;
            em_andamento) ic="🔄" ;;
            falhou)      ic="💥" ;;
            pendente)    ic="⏳" ;;
            *)           ic="❓" ;;
        esac
        echo "| $id | $projeto | $descricao | $ic $status | $tipo |"
    done
    echo ""

    # Total
    TOTAL=$(jq '.tarefas | length' "$TASKS_FILE")
    CONCLUIDAS=$(jq '[.tarefas[] | select(.status == "concluido")] | length' "$TASKS_FILE")
    CANCELADAS=$(jq '[.tarefas[] | select(.status == "cancelado")] | length' "$TASKS_FILE")
    PENDENTES=$(jq '[.tarefas[] | select(.status == "pendente")] | length' "$TASKS_FILE")
    echo "**Total:** $TOTAL tarefas ($CONCLUIDAS concluídas, $CANCELADAS canceladas, $PENDENTES pendentes)"
    echo ""

    # Projetos afetados
    echo "## Projetos Afetados"
    echo ""
    echo "| Projeto | Tasks |"
    echo "|---------|-------|"
    # Extrair projetos com prefixo comum
    for proj in $(jq -r '.tarefas[].projeto' "$TASKS_FILE" | sort -u); do
        proj_short=$(echo "$proj" | sed 's|.*/||')
        tasks=$(jq -r --arg p "$proj" '[.tarefas[] | select(.projeto == $p) | .id] | sort | join(", ")' "$TASKS_FILE")
        echo "| $proj_short | $tasks |"
    done
    echo ""

    # Dependências (grafo simplificado)
    echo "## Dependências"
    echo ""
    echo '```'
    # Gerar grafo de dependências
    jq -r '.tarefas[] | select(.dependeDe | length > 0) | .id + " ← " + (.dependeDe | join(", "))' "$TASKS_FILE" | sort
    echo '```'
    echo ""

    # Informacao de commits (se existir)
    if jq -e '.tarefas[0].commitHash' "$TASKS_FILE" > /dev/null 2>&1; then
        echo "## Commits"
        echo ""
        echo "| Projeto | Commit Hash | Branch |"
        echo "|---------|-------------|--------|"
        for proj in $(jq -r '.tarefas[].projeto' "$TASKS_FILE" | sort -u); do
            hash=$(jq -r --arg p "$proj" '[.tarefas[] | select(.projeto == $p and .commitHash != null) | .commitHash] | first // "-"' "$TASKS_FILE")
            echo "| $proj | \`$hash\` | \`feature/$TICKET_ID\` |"
        done
        echo ""
    fi

    # Observacoes (preservar existentes)
    if [[ -n "$OBSERVACOES" ]]; then
        echo "## Observações"
        echo ""
        echo "$OBSERVACOES"
    fi
} > "$CONTEXT_FILE"

echo "Contexto gerado: $CONTEXT_FILE"
echo "  Total: $TOTAL | Concluidas: $CONCLUIDAS | Canceladas: $CANCELADAS | Pendentes: $PENDENTES"
