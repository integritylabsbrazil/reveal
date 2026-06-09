#!/usr/bin/env bash
# Gera status-tasks.json e implementation-plan.md a partir de jira-data.json
# Uso: ./generate-tasks.sh TICKET_DIR [--granularity grossa|media|fina] [--from-jira] [--preview] [--interactive]
#
# Flags:
#   --from-jira   Gera tasks a partir das subtasks reais do Jira (auto-detectado se houver subtasks)
#   --granularity Usa granularidade classica (grossa/media/fina) — ignorado se --from-jira ativo
#   --preview     Apenas mostra preview sem gerar arquivos
#   --interactive Mostra preview e permite ajustar tasks antes de gerar
#   --suggest     Apenas sugere granularidade sem gerar tasks

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REVEAL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    cat <<EOF
Uso: $0 TICKET_DIR [OPCOES]

Opcoes:
  --granularity grossa|media|fina  Forcar granularidade (auto-detectado se omitido)
  --from-jira                      Gerar tasks a partir das subtasks do Jira
  --preview                        Apenas mostrar preview sem gerar arquivos
  --interactive                    Mostrar preview e permitir ajustes antes de gerar
  --suggest                        Apenas sugerir granularidade
  --help                           Exibir esta ajuda

Exemplos:
  $0 tickets/PROJ-123
  $0 tickets/PROJ-123 --preview
  $0 tickets/PROJ-123 --interactive
  $0 tickets/PROJ-123 --suggest
EOF
    exit 0
}

if [ $# -lt 1 ]; then
    usage
fi

TICKET_DIR="$1"
shift

# Extrair flags opcionais
GRANULARITY=""
PREVIEW=""
FROM_JIRA=""
INTERACTIVE=""
SUGGEST=""

while [ $# -gt 0 ]; do
    case "$1" in
        --granularity)
            GRANULARITY="$2"
            shift 2
            ;;
        --granularity=*)
            GRANULARITY="${1#*=}"
            shift
            ;;
        --from-jira)
            FROM_JIRA="--from-jira"
            shift
            ;;
        --preview)
            PREVIEW="--preview"
            shift
            ;;
        --interactive)
            INTERACTIVE="true"
            shift
            ;;
        --suggest)
            SUGGEST="true"
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            shift
            ;;
    esac
done

# Auto-detect: se jira-data.json tem subtasks e nenhuma flag foi passada, usa --from-jira
if [ -z "$GRANULARITY" ] && [ -z "$FROM_JIRA" ] && [ -z "$SUGGEST" ]; then
    SUB_COUNT=$(jq '.subtasks | length' "$TICKET_DIR/jira-data.json" 2>/dev/null || echo 0)
    if [ "$SUB_COUNT" -gt 0 ]; then
        FROM_JIRA="--from-jira"
    fi
fi

if [ ! -f "$TICKET_DIR/jira-data.json" ]; then
    echo "ERRO: $TICKET_DIR/jira-data.json nao encontrado"
    exit 1
fi

# Auto-descobrir config
CONFIG=""
if [ -f "$REVEAL_DIR/refine-config.local.json" ]; then
    CONFIG="$REVEAL_DIR/refine-config.local.json"
elif [ -f "$REVEAL_DIR/refine-config.json" ]; then
    CONFIG="$REVEAL_DIR/refine-config.json"
fi

# --suggest: apenas mostrar sugestao de granularidade
if [ -n "$SUGGEST" ]; then
    echo "[TASKS] Analisando ticket para sugerir granularidade..."
    if [ -n "$CONFIG" ]; then
        python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from generate_tasks import suggest_granularity, get_change_keywords
from utils import load_json
import json, os

ticket_dir = '$TICKET_DIR'
jira_data = load_json(os.path.join(ticket_dir, 'jira-data.json'))
if not jira_data:
    print('ERRO: jira-data.json nao encontrado')
    sys.exit(1)

keywords = get_change_keywords(jira_data)
scan_data = load_json(os.path.join(ticket_dir, 'impact-report.json'))
if isinstance(scan_data, list):
    scan_data = scan_data[0] if scan_data else {}

gran, motivo = suggest_granularity(keywords, jira_data, scan_data)

# Mostrar detalhes
active_kw = [k for k, v in keywords.items() if v and k != 'needs_test']
print(f'')
print(f'Palavras-chave ativas: {len(active_kw)}')
for k, v in keywords.items():
    if v and k != 'needs_test':
        print(f'  - {k}')
print(f'')
print(f'Granularidade sugerida: {gran}')
print(f'Motivo: {motivo}')
" 2>&1
    else
        python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from generate_tasks import suggest_granularity, get_change_keywords
from utils import load_json
import json, os

ticket_dir = '$TICKET_DIR'
jira_data = load_json(os.path.join(ticket_dir, 'jira-data.json'))
if not jira_data:
    print('ERRO: jira-data.json nao encontrado')
    sys.exit(1)

keywords = get_change_keywords(jira_data)

gran, motivo = suggest_granularity(keywords, jira_data, None)
print(f'Granularidade sugerida: {gran}')
print(f'Motivo: {motivo}')
" 2>&1
    fi
    exit 0
fi

# Montar argumentos extras
EXTRA_ARGS=""
[ -n "$GRANULARITY" ] && EXTRA_ARGS="$EXTRA_ARGS --granularity $GRANULARITY"
[ -n "$FROM_JIRA" ] && EXTRA_ARGS="$EXTRA_ARGS $FROM_JIRA"
[ -n "$PREVIEW" ] && EXTRA_ARGS="$EXTRA_ARGS $PREVIEW"

# Funcao para executar o python
run_python() {
    if [ -n "$CONFIG" ]; then
        # shellcheck disable=SC2086
        python3 "$SCRIPT_DIR/generate_tasks.py" "$TICKET_DIR" "$CONFIG" $EXTRA_ARGS
    else
        # shellcheck disable=SC2086
        python3 "$SCRIPT_DIR/generate_tasks.py" "$TICKET_DIR" $EXTRA_ARGS
    fi
}

# ============================================================
# MODO INTERATIVO
# ============================================================
if [ -n "$INTERACTIVE" ]; then
    echo ""
    echo "============================================"
    echo " Modo Interativo — Ajuste de Tasks"
    echo "============================================"
    echo ""

    while true; do
        # Mostrar preview
        echo "--- Preview das Tasks ---"
        PREVIEW="--preview" EXTRA_ARGS="$EXTRA_ARGS --preview"
        run_python 2>&1 | grep -v "^$"  # hide empty lines
        echo ""

        echo "Opcoes:"
        echo "  g) Alterar granularidade"
        echo "  d) Detalhar uma task"
        echo "  c) Confirmar e gerar"
        echo "  x) Cancelar"
        read -r -p "Escolha: " choice

        case "$choice" in
            g|G)
                echo ""
                echo "Granularidades disponiveis:"
                echo "  1) Grossa (3 tasks)"
                echo "  2) Media (6-7 tasks)"
                echo "  3) Fina (10-11 tasks)"
                read -r -p "Escolha (1-3): " gchoice
                case "$gchoice" in
                    1) GRANULARITY="grossa"; echo "Granularidade alterada para: grossa" ;;
                    2) GRANULARITY="media"; echo "Granularidade alterada para: media" ;;
                    3) GRANULARITY="fina"; echo "Granularidade alterada para: fina" ;;
                    *) echo "Opcao invalida" ;;
                esac
                EXTRA_ARGS=""
                [ -n "$GRANULARITY" ] && EXTRA_ARGS="$EXTRA_ARGS --granularity $GRANULARITY"
                [ -n "$FROM_JIRA" ] && EXTRA_ARGS="$EXTRA_ARGS $FROM_JIRA"
                ;;
            d|D)
                echo ""
                read -r -p "ID da task para detalhar: " tid
                if [ -n "$tid" ]; then
                    python3 -c "
import json, sys
f = open('$TICKET_DIR/status-tasks.json')
data = json.load(f)
found = [t for t in data.get('tarefas', []) if t.get('id') == '$tid']
if found:
    t = found[0]
    print(f'ID: {t.get(\"id\")}')
    print(f'Descricao: {t.get(\"descricao\")}')
    print(f'Nivel: {t.get(\"nivel\")}')
    print(f'Tipo: {t.get(\"tipo\")}')
    print(f'Status: {t.get(\"status\")}')
    print(f'Depende de: {t.get(\"dependeDe\", [])}')
    est = t.get('esforcoEstimado', {})
    if est:
        print(f'Esforco: {est.get(\"descricao\")}')
    print(f'')
    print('--- Observacoes ---')
    print(t.get('observacoes', '(nenhuma)')[:300])
else:
    print(f'Task $tid nao encontrada')
" 2>&1
                fi
                echo ""
                read -r -p "Pressione ENTER para continuar..."
                ;;
            c|C)
                echo ""
                echo "Confirmando e gerando tasks..."
                PREVIEW=""
                EXTRA_ARGS=""
                [ -n "$GRANULARITY" ] && EXTRA_ARGS="$EXTRA_ARGS --granularity $GRANULARITY"
                [ -n "$FROM_JIRA" ] && EXTRA_ARGS="$EXTRA_ARGS $FROM_JIRA"
                run_python
                break
                ;;
            x|X)
                echo "Cancelado pelo usuario"
                exit 0
                ;;
            *)
                echo "Opcao invalida"
                ;;
        esac
        echo ""
    done
    exit 0
fi

# ============================================================
# MODO NORMAL (nao interativo)
# ============================================================

# No preview mode, stop after printing tasks
if [ -n "$PREVIEW" ]; then
    run_python
    exit 0
fi

# Gerar tasks
run_python

# Gerar implementation-plan.md via Python
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

# Gerar AGENTS-EXEC.md (instrucoes de execucao)
if [ -f "$SCRIPT_DIR/generate_agents_exec.py" ]; then
    python3 "$SCRIPT_DIR/generate_agents_exec.py" "$TICKET_DIR" 2>/dev/null || true
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
