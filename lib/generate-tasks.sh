#!/usr/bin/env bash
# Gera status-tasks.json e implementation-plan.md a partir de jira-data.json
# Uso: ./generate-tasks.sh TICKET_DIR

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REVEAL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ $# -lt 1 ]; then
    echo "Uso: $0 TICKET_DIR"
    exit 1
fi

TICKET_DIR="$1"

if [ ! -f "$TICKET_DIR/jira-data.json" ]; then
    echo "ERRO: $TICKET_DIR/jira-data.json nao encontrado"
    exit 1
fi

# Auto-descobrir config: local > template
CONFIG=""
if [ -f "$REVEAL_DIR/refine-config.local.json" ]; then
    CONFIG="$REVEAL_DIR/refine-config.local.json"
elif [ -f "$REVEAL_DIR/refine-config.json" ]; then
    CONFIG="$REVEAL_DIR/refine-config.json"
fi

if [ -n "$CONFIG" ]; then
    python3 "$SCRIPT_DIR/generate_tasks.py" "$TICKET_DIR" "$CONFIG"
else
    python3 "$SCRIPT_DIR/generate_tasks.py" "$TICKET_DIR"
fi

# Gerar implementation-plan.md rico via Python (sobrescreve sempre)
if [ -f "$SCRIPT_DIR/generate_implementation_plan.py" ]; then
    python3 "$SCRIPT_DIR/generate_implementation_plan.py" "$TICKET_DIR" 2>/dev/null || {
        echo "[WARN] Falha ao gerar implementation-plan.md, usando fallback" >&2
    }
fi
# Fallback: se nao foi gerado ainda, criar placeholder basico
if [ ! -f "$TICKET_DIR/implementation-plan.md" ]; then
    TICKET_ID=$(jq -r '.ticketId // "TICKET"' "$TICKET_DIR/jira-data.json" 2>/dev/null || echo "TICKET")
    cat > "$TICKET_DIR/implementation-plan.md" << PLAN
# Plano de Implementacao — $TICKET_ID

## Arquitetura
- Conforme especificacao tecnica no Jira

## Projetos Envolvidos
$(jq -r '.projetosEnvolvidos[] | "- " + .' "$TICKET_DIR/status-tasks.json" 2>/dev/null || echo "- pendente")
PLAN
fi

# Gerar contexto-implementacao.md
if [ -f "$REVEAL_DIR/generate-context.sh" ]; then
    TICKET_ID=$(jq -r '.ticketId // "DESCONHECIDO"' "$TICKET_DIR/jira-data.json" 2>/dev/null || echo "DESCONHECIDO")
    bash "$REVEAL_DIR/generate-context.sh" "$TICKET_ID" 2>/dev/null || true
fi

# Validar
if [ -f "$REVEAL_DIR/validate-ticket.sh" ]; then
    TICKET_ID=$(jq -r '.ticketId // "DESCONHECIDO"' "$TICKET_DIR/jira-data.json" 2>/dev/null || echo "DESCONHECIDO")
    bash "$REVEAL_DIR/validate-ticket.sh" "$TICKET_ID" 2>/dev/null || true
fi
