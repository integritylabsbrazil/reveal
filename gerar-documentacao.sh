#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_PREFIX="DOC"
source "$SCRIPT_DIR/lib/utils.sh"

run() {
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "[DRY-RUN] skipparia: $*"
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
    log_warn "MODO DRY-RUN: Nenhuma alteracao sera feita."
fi

# ============================================================
# 1. Verificar setup (credenciais, config)
# ============================================================
log_section "Verificando Configuracao"

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
        log_ok "Credenciais carregadas de ~/.jira-credentials"
    else
        log_warn "Variaveis de ambiente nao configuradas."
        log_warn "Execute setup.sh primeiro ou configure manualmente:"
        echo "  export JIRA_USER=email@empresa.com"
        echo "  export JIRA_TOKEN=seu-token"
        echo "  export JIRA_BASE=https://meujira.atlassian.net"
        echo ""
        read -r -p "Deseja executar setup.sh agora? (s/N): " RUN_SETUP
        if [[ "$RUN_SETUP" =~ ^[Ss]$ ]]; then
            bash "$SCRIPT_DIR/setup.sh"
        else
            log_error "Setup necessario. Abortando."
            exit 1
        fi
    fi
else
    log_ok "Variaveis de ambiente ja configuradas"
fi

# ============================================================
# 2. Verificar refine-config.local.json
# ============================================================
LOCAL_CONFIG="$SCRIPT_DIR/refine-config.local.json"
if [[ ! -f "$LOCAL_CONFIG" ]]; then
    log_warn "refine-config.local.json nao encontrado."
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "[DRY-RUN] Usaria refine-config.json como base para criar $LOCAL_CONFIG"
    elif [[ -f "$SCRIPT_DIR/refine-config.json" ]]; then
        jq --arg base "$JIRA_BASE" \
           '.jira.baseUrl = $base' "$SCRIPT_DIR/refine-config.json" > "$LOCAL_CONFIG"
        log_ok "refine-config.local.json criado"
    else
        log_error "refine-config.json nao encontrado!"
        exit 1
    fi
fi

# ============================================================
# 3. Confirmar se ticket ja existe
# ============================================================
TICKET_DIR="$SCRIPT_DIR/tickets/$TICKET_ID"
if [[ -d "$TICKET_DIR" ]] && [[ -n "$(ls -A "$TICKET_DIR" 2>/dev/null)" ]]; then
    log_warn "O diretorio $TICKET_DIR ja existe e contem dados."
    if [[ "$DRY_RUN" != true ]]; then
        read -r -p "Deseja sobrescrever? (s/N): " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Ss]$ ]]; then
            log_error "Abortando pelo usuario."
            exit 1
        fi
        rm -rf "$TICKET_DIR" 2>/dev/null || true
        mkdir -p "$TICKET_DIR"
    else
        log_warn "[DRY-RUN] Sobrescreveria $TICKET_DIR"
    fi
fi

# ============================================================
# 4. Pipeline completa
# ============================================================
log_section "Pipeline de Documentacao — $TICKET_ID"

log_ok "Iniciando pipeline: fetch → scan → perguntas → refinamento → validacao"

# Etapas (refinement temporario sem tasks — ainda nao geradas)
run bash "$SCRIPT_DIR/refine-ticket.sh" "$TICKET_ID" --refine

# ============================================================
# 5. Geracao automatica de subtarefas + plano + re-refinamento
# ============================================================
if [[ -f "$SCRIPT_DIR/lib/generate-tasks.sh" && -f "$TICKET_DIR/jira-data.json" ]]; then
    log_section "Geracao de Subtarefas"
    # Sempre passar --from-jira: o pipeline ja buscou os dados do Jira
    run bash "$SCRIPT_DIR/lib/generate-tasks.sh" "$TICKET_DIR" --from-jira
    log_ok "Subtarefas geradas em status-tasks.json"

    # Gerar plano de implementacao agora que status-tasks.json existe
    log_section "Gerando Plano de Implementacao"
    run bash "$SCRIPT_DIR/refine-ticket.sh" "$TICKET_ID" --plan 2>/dev/null || true
    log_ok "Plano de implementacao gerado"

    # Re-gerar refinamento agora com as subtarefas
    log_section "Re-gerando refinamento com subtarefas"
    run bash "$SCRIPT_DIR/refine-ticket.sh" "$TICKET_ID" --refinement 2>/dev/null || true
    log_ok "Refinamento atualizado com subtarefas"
fi

# ============================================================
# 5.5. Gerar AGENTS-EXEC.md
# ============================================================
if [[ -f "$SCRIPT_DIR/lib/generate_agents_exec.py" && -f "$TICKET_DIR/status-tasks.json" ]]; then
    run python3 "$SCRIPT_DIR/lib/generate_agents_exec.py" "$TICKET_DIR" 2>/dev/null || true
    log_ok "AGENTS-EXEC.md gerado"
fi

# ============================================================
# 6. Pos-processamento
# ============================================================
log_section "Pos-processamento"

if [[ -f "$SCRIPT_DIR/validate-ticket.sh" ]]; then
    run bash "$SCRIPT_DIR/validate-ticket.sh" "$TICKET_ID" 2>/dev/null || true
    log_ok "Validacao concluida"
fi

if [[ -f "$SCRIPT_DIR/generate-context.sh" ]]; then
    run bash "$SCRIPT_DIR/generate-context.sh" "$TICKET_ID" 2>/dev/null || true
    log_ok "Contexto de implementacao atualizado"
fi

if [[ -f "$SCRIPT_DIR/generate-index.sh" ]]; then
    run bash "$SCRIPT_DIR/generate-index.sh" 2>/dev/null || true
    log_ok "Indice atualizado"
fi

# ============================================================
# 6.5. Geracao de especificacao OpenAPI (se aplicavel)
# ============================================================
if [[ -f "$SCRIPT_DIR/lib/generate_openapi_spec.py" && -f "$TICKET_DIR/status-tasks.json" ]]; then
    log_section "Gerando Especificacao OpenAPI"
    OPENAPI_OUTPUT=$(python3 "$SCRIPT_DIR/lib/generate_openapi_spec.py" "$TICKET_DIR" 2>&1 || true)
    if echo "$OPENAPI_OUTPUT" | grep -q "openapi.yaml gerado"; then
        log_ok "openapi.yaml gerado"
        if [[ -f "$TICKET_DIR/openapi.yaml" ]]; then
            ENDPOINT_COUNT=$(python3 -c "import yaml; d=yaml.safe_load(open('$TICKET_DIR/openapi.yaml')); print(len(d.get('paths', {})))" 2>/dev/null || echo "0")
            SCHEMA_COUNT=$(python3 -c "import yaml; d=yaml.safe_load(open('$TICKET_DIR/openapi.yaml')); print(len(d.get('components', {}).get('schemas', {})))" 2>/dev/null || echo "0")
            echo "    Endpoints documentados: ${ENDPOINT_COUNT}"
            echo "    Schemas documentados: ${SCHEMA_COUNT}"
        fi
    else
        log_info "Ticket sem envolvimento de API — openapi.yaml nao gerado."
    fi
fi

# ============================================================
# 7. Atualizacao da Descricao no Jira (interativa)
# ============================================================
if [[ -f "$SCRIPT_DIR/lib/jira-update-description.sh" && -f "$TICKET_DIR/status-tasks.json" ]]; then
    UPDATE_SCRIPT="$SCRIPT_DIR/lib/jira-update-description.sh"
    echo ""
    log_info "A especificacao do ticket sera inserida na descricao do Jira"
    echo "  (sem criacao de subtasks — tudo no description do ticket principal)"
    echo ""
    read -r -p "Deseja atualizar a descricao do ticket $TICKET_ID no Jira agora? (s/N) " UPDATE_REPLY
    case "$UPDATE_REPLY" in
        s|S|sim|SIM)
            run bash "$UPDATE_SCRIPT" "$TICKET_ID"
            log_ok "Descricao do ticket $TICKET_ID atualizada no Jira"
            ;;
        *)
            log_info "Atualizacao da descricao pulada."
            echo "  Para fazer depois: bash lib/jira-update-description.sh $TICKET_ID"
            echo "  Para preview sem enviar: bash lib/jira-update-description.sh $TICKET_ID --dry-run"
            ;;
    esac
    echo ""
fi

# ============================================================
# 8. Resumo
# ============================================================
log_section "Documentacao Gerada — $TICKET_ID"

echo ""
echo "  Diretorio: $TICKET_DIR"
echo ""
echo "  Arquivos gerados:"
for f in jira-data.json jira-summary.md impact-report.json \
         perguntas-negocio.md perguntas-negocio.json \
         refinamento-tecnico.md status-tasks.json \
         implementation-plan.md contexto-implementacao.md \
         AGENTS-EXEC.md openapi.yaml; do
    if [[ -f "$TICKET_DIR/$f" ]]; then
        echo "    ✅ $f"
    else
        echo "    ⬜ $f (nao gerado)"
    fi
done
echo ""
echo "  Novas funcionalidades disponiveis:"
echo "    🎯 Granularidade inteligente — auto-detectarada baseada na complexidade"
echo "    🧩 Observacoes enriquecidas — com contexto real do projeto (projects-context/)"
echo "    📊 Score de qualidade — avaliacao automatica no validate-ticket.sh"
echo "    📈 Grafo de dependencias Mermaid — visualizacao das dependencias entre tasks"
echo "    ⏱ Estimativa de esforco — horas estimadas por task e total"
echo ""
echo "  Proximos passos:"
echo "    1. Revise perguntas-negocio.md e envie ao PO"
echo "    2. Com as respostas, refine implementation-plan.md e status-tasks.json"
echo "    3. Copie refinamento-tecnico.md para o Jira (campo de especificacao)"
echo "    4. Se houver openapi.yaml, revise e anexe ao Jira (via update-description)"
echo "    5. Inicie a implementacao via AGENTS.md ou repasse para o time dev"
echo ""
log_ok "Concluido!"
