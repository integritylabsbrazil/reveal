#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; BLUE='\033[34m'; CYAN='\033[36m'; NC='\033[0m'

info()    { echo -e "${BLUE}[DOC]${NC} $1"; }
ok()      { echo -e "${GREEN}[DOC]${NC} $1"; }
warn()    { echo -e "${YELLOW}[DOC]${NC} $1"; }
error()   { echo -e "${RED}[DOC]${NC} $1"; }
section() { echo ""; echo -e "${CYAN}═══════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}═══════════════════════════════════════${NC}"; echo ""; }

run() {
    if [[ "$DRY_RUN" == true ]]; then
        warn "[DRY-RUN] skipparia: $*"
    else
        "$@"
    fi
}

usage() {
    cat <<EOF
Uso: $0 TICKET_ID

Gera documentacao completa de um ticket Jira:
  - Busca dados do Jira (deep fetch com épico, links, comentários)
  - Escaneia o codigo fonte do projeto
  - Gera perguntas para o negocio
  - Cria documento de refinamento tecnico
  - Valida consistencia dos documentos
  - Atualiza o índice de tickets

Exemplos:
  $0 SPR-3417
  $0 PROJ-123

Variaveis de ambiente:
  JIRA_USER, JIRA_TOKEN, JIRA_BASE  (ou execute setup.sh primeiro)
EOF
    exit 0
}

DRY_RUN=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --help|-h) usage ;;
        *) ARGS+=("$arg") ;;
    esac
done

if [[ ${#ARGS[@]} -ne 1 ]]; then
    usage
fi

TICKET_ID="${ARGS[0]}"

if [[ "$DRY_RUN" == true ]]; then
    warn "MODO DRY-RUN: Nenhuma alteracao sera feita."
fi

# ============================================================
# 1. Verificar setup (credenciais, config)
# ============================================================
section "Verificando Configuracao"

if [[ -z "${JIRA_USER:-}" || -z "${JIRA_TOKEN:-}" || -z "${JIRA_BASE:-}" ]]; then
    if [[ -f "$HOME/.jira-credentials" ]]; then
        IFS=':' read -r JIRA_USER JIRA_TOKEN < "$HOME/.jira-credentials"
        JIRA_BASE="${JIRA_BASE:-}"
        if [[ -z "$JIRA_BASE" ]]; then
            JIRA_BASE=$(jq -r '.jira.baseUrl // ""' "$SCRIPT_DIR/refine-config.local.json" 2>/dev/null || true)
        fi
        if [[ -z "$JIRA_BASE" ]]; then
            JIRA_BASE=$(jq -r '.jira.baseUrl // ""' "$SCRIPT_DIR/refine-config.json" 2>/dev/null || true)
        fi
        export JIRA_USER JIRA_TOKEN JIRA_BASE
        ok "Credenciais carregadas de ~/.jira-credentials"
    else
        warn "Variaveis de ambiente nao configuradas."
        warn "Execute setup.sh primeiro ou configure manualmente:"
        echo "  export JIRA_USER=email@empresa.com"
        echo "  export JIRA_TOKEN=seu-token"
        echo "  export JIRA_BASE=https://meujira.atlassian.net"
        echo ""
        read -r -p "Deseja executar setup.sh agora? (s/N): " RUN_SETUP
        if [[ "$RUN_SETUP" =~ ^[Ss]$ ]]; then
            bash "$SCRIPT_DIR/setup.sh"
        else
            error "Setup necessario. Abortando."
            exit 1
        fi
    fi
else
    ok "Variaveis de ambiente ja configuradas"
fi

# ============================================================
# 2. Verificar refine-config.local.json
# ============================================================
LOCAL_CONFIG="$SCRIPT_DIR/refine-config.local.json"
if [[ ! -f "$LOCAL_CONFIG" ]]; then
    warn "refine-config.local.json nao encontrado."
    if [[ "$DRY_RUN" == true ]]; then
        warn "[DRY-RUN] Usaria refine-config.json como base para criar $LOCAL_CONFIG"
    elif [[ -f "$SCRIPT_DIR/refine-config.json" ]]; then
        jq --arg base "$JIRA_BASE" \
           '.jira.baseUrl = $base' "$SCRIPT_DIR/refine-config.json" > "$LOCAL_CONFIG"
        ok "refine-config.local.json criado"
    else
        error "refine-config.json nao encontrado!"
        exit 1
    fi
fi

# ============================================================
# 3. Confirmar se ticket ja existe
# ============================================================
TICKET_DIR="$SCRIPT_DIR/tickets/$TICKET_ID"
if [[ -d "$TICKET_DIR" ]] && [[ -n "$(ls -A "$TICKET_DIR" 2>/dev/null)" ]]; then
    warn "O diretorio $TICKET_DIR ja existe e contem dados."
    if [[ "$DRY_RUN" != true ]]; then
        read -r -p "Deseja sobrescrever? (s/N): " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Ss]$ ]]; then
            error "Abortando pelo usuario."
            exit 1
        fi
        rm -rf "$TICKET_DIR" 2>/dev/null || true
        mkdir -p "$TICKET_DIR"
    else
        warn "[DRY-RUN] Sobrescreveria $TICKET_DIR"
    fi
fi

# ============================================================
# 4. Pipeline completa
# ============================================================
section "Pipeline de Documentacao — $TICKET_ID"

ok "Iniciando pipeline: fetch → scan → perguntas → refinamento → validacao"

# Etapas (refinement temporario sem tasks — ainda nao geradas)
run bash "$SCRIPT_DIR/refine-ticket.sh" "$TICKET_ID" --refine

# ============================================================
# 5. Geracao automatica de subtarefas + re-refinamento
# ============================================================
if [[ -f "$SCRIPT_DIR/lib/generate-tasks.sh" && -f "$TICKET_DIR/jira-data.json" ]]; then
    section "Geracao de Subtarefas"
    run bash "$SCRIPT_DIR/lib/generate-tasks.sh" "$TICKET_DIR"
    ok "Subtarefas geradas em status-tasks.json"

    # Re-gerar refinamento agora com as subtarefas
    section "Re-gerando refinamento com subtarefas"
    run bash "$SCRIPT_DIR/refine-ticket.sh" "$TICKET_ID" --refinement 2>/dev/null || true
    ok "Refinamento atualizado com subtarefas"
fi

# ============================================================
# 6. Pos-processamento
# ============================================================
section "Pos-processamento"

if [[ -f "$SCRIPT_DIR/validate-ticket.sh" ]]; then
    run bash "$SCRIPT_DIR/validate-ticket.sh" "$TICKET_ID" 2>/dev/null || true
    ok "Validacao concluida"
fi

if [[ -f "$SCRIPT_DIR/generate-context.sh" ]]; then
    run bash "$SCRIPT_DIR/generate-context.sh" "$TICKET_ID" 2>/dev/null || true
    ok "Contexto de implementacao atualizado"
fi

if [[ -f "$SCRIPT_DIR/generate-index.sh" ]]; then
    run bash "$SCRIPT_DIR/generate-index.sh" 2>/dev/null || true
    ok "Indice atualizado"
fi

# ============================================================
# 6. Resumo
# ============================================================
section "Documentacao Gerada — $TICKET_ID"

echo ""
echo "  Diretorio: $TICKET_DIR"
echo ""
echo "  Arquivos gerados:"
for f in jira-data.json jira-summary.md impact-report.json \
         perguntas-negocio.md perguntas-negocio.json \
         refinamento-tecnico.md status-tasks.json \
         implementation-plan.md contexto-implementacao.md; do
    if [[ -f "$TICKET_DIR/$f" ]]; then
        echo "    ✅ $f"
    else
        echo "    ⬜ $f (nao gerado)"
    fi
done
echo ""
echo "  Proximos passos:"
echo "    1. Revise perguntas-negocio.md e envie ao PO"
echo "    2. Com as respostas, refine implementation-plan.md e status-tasks.json"
echo "    3. Copie refinamento-tecnico.md para o Jira (campo de especificacao)"
echo "    4. Inicie a implementacao via AGENTS.md ou repasse para o time dev"
echo ""
ok "Concluido!"
