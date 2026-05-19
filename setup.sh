#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; BLUE='\033[34m'; CYAN='\033[36m'; NC='\033[0m'

info()  { echo -e "${BLUE}[SETUP]${NC} $1"; }
ok()    { echo -e "${GREEN}[SETUP]${NC} $1"; }
warn()  { echo -e "${YELLOW}[SETUP]${NC} $1"; }
error() { echo -e "${RED}[SETUP]${NC} $1"; }
section() { echo ""; echo -e "${CYAN}═══════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}═══════════════════════════════════════${NC}"; echo ""; }

CONFIG_FILE="$SCRIPT_DIR/refine-config.json"
LOCAL_CONFIG="$SCRIPT_DIR/refine-config.local.json"

section "Setup do Reveal — Configuracao Inicial"

# ============================================================
# 1. Dependencias de Sistema
# ============================================================
info "Verificando dependencias de sistema..."

MISSING=()
for cmd in curl jq python3; do
    if command -v "$cmd" &> /dev/null; then
        ok "  $cmd encontrado"
    else
        error "  $cmd NAO encontrado"
        MISSING+=("$cmd")
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo ""
    warn "Dependencias faltando. Instale com:"
    echo "  sudo apt-get install ${MISSING[*]}"
    exit 1
fi

# ============================================================
# 2. Configurar Jira
# ============================================================
section "Configuracao do Jira"

# Extrair JIRA_BASE do config
JIRA_BASE="${JIRA_BASE:-}"
if [[ -z "$JIRA_BASE" ]]; then
    JIRA_BASE=$(jq -r '.jira.baseUrl // ""' "$CONFIG_FILE" 2>/dev/null || true)
fi

if [[ -z "$JIRA_BASE" ]]; then
    read -r -p "URL base do Jira (ex: https://meujira.atlassian.net): " JIRA_BASE
fi

if [[ -z "$JIRA_BASE" ]]; then
    error "JIRA_BASE e obrigatorio"
    exit 1
fi
export JIRA_BASE
ok "JIRA_BASE: $JIRA_BASE"

# Credenciais — tentar ATLASSIAN_USER/ATLASSIAN_TOKEN primeiro
JIRA_USER="${JIRA_USER:-}"
JIRA_TOKEN="${JIRA_TOKEN:-}"

if [[ -z "$JIRA_USER" && -n "${ATLASSIAN_USER:-}" ]]; then
    JIRA_USER="$ATLASSIAN_USER"
    ok "JIRA_USER herdado de ATLASSIAN_USER"
fi
if [[ -z "$JIRA_TOKEN" && -n "${ATLASSIAN_TOKEN:-}" ]]; then
    JIRA_TOKEN="$ATLASSIAN_TOKEN"
    ok "JIRA_TOKEN herdado de ATLASSIAN_TOKEN"
fi

# Se ainda faltar, tentar ~/.jira-credentials
if [[ -z "$JIRA_USER" || -z "$JIRA_TOKEN" ]]; then
    if [[ -f "$HOME/.jira-credentials" ]]; then
        IFS=':' read -r JIRA_USER JIRA_TOKEN < "$HOME/.jira-credentials"
        ok "Credenciais carregadas de ~/.jira-credentials"
    fi
fi

# Se ainda faltar, pedir interativamente
if [[ -z "$JIRA_USER" ]]; then
    read -r -p "Email/usuario Jira: " JIRA_USER
fi
if [[ -z "$JIRA_TOKEN" ]]; then
    read -r -s -p "Token de API Jira: " JIRA_TOKEN
    echo ""
fi

if [[ -z "$JIRA_USER" || -z "$JIRA_TOKEN" ]]; then
    error "JIRA_USER e JIRA_TOKEN sao obrigatorios"
    exit 1
fi

export JIRA_USER JIRA_TOKEN
ok "Credenciais Jira configuradas"

# Salvar ~/.jira-credentials se nao existir
if [[ ! -f "$HOME/.jira-credentials" ]]; then
    echo "${JIRA_USER}:${JIRA_TOKEN}" > "$HOME/.jira-credentials"
    chmod 600 "$HOME/.jira-credentials"
    ok "Credenciais salvas em ~/.jira-credentials (chmod 600)"
fi

# Exportar para ambiente tambem como ATLASSIAN_* para compatibilidade
export ATLASSIAN_USER="$JIRA_USER"
export ATLASSIAN_TOKEN="$JIRA_TOKEN"

# ============================================================
# 3. Validar credenciais com um ping no Jira
# ============================================================
section "Validando conexao com Jira"

HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
    -u "$JIRA_USER:$JIRA_TOKEN" \
    -H "Accept: application/json" \
    "$JIRA_BASE/rest/api/3/myself" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
    ok "Conexao Jira OK (HTTP 200)"
elif [[ "$HTTP_CODE" == "401" ]]; then
    error "Conexao Jira: HTTP 401 — Credenciais invalidas"
    exit 1
elif [[ "$HTTP_CODE" == "403" ]]; then
    error "Conexao Jira: HTTP 403 — Acesso negado"
    exit 1
else
    warn "Conexao Jira: HTTP $HTTP_CODE (pode ser problema de rede/URL)"
fi

# ============================================================
# 4. Configurar Projetos
# ============================================================
section "Configuracao dos Projetos"

# Extrair caminhos dos projetos do config
PROJECT_PATHS=()
while IFS= read -r p; do
    PROJECT_PATHS+=("$p")
done < <(jq -r '.projects[].path // empty' "$CONFIG_FILE")

if [[ ${#PROJECT_PATHS[@]} -eq 0 ]]; then
    warn "Nenhum projeto configurado em refine-config.json"
    warn "Adicione projetos manualmente ou crie refine-config.local.json"
fi

ALL_EXIST=true
for p_path in "${PROJECT_PATHS[@]}"; do
    ABS_PATH=$(cd "$SCRIPT_DIR/$p_path" 2>/dev/null && pwd || true)
    if [[ -z "$ABS_PATH" ]]; then
        warn "Projeto NAO encontrado: $SCRIPT_DIR/$p_path"
        ALL_EXIST=false
    else
        ok "Projeto encontrado: $ABS_PATH"
    fi
done

if [[ "$ALL_EXIST" == false ]]; then
    echo ""
    warn "Alguns projetos nao existem. Voce pode:"
    echo "  1. Criar os diretorios: mkdir -p $SCRIPT_DIR/../projetos/{backend-java,frontend-web}"
    echo "  2. Ou ajustar os caminhos em refine-config.local.json"
    echo "  3. Ou continuar (code scan sera pulado automaticamente)"
    echo ""
    read -r -p "Criar diretorios de projeto agora? (s/N): " CREATE_DIRS
    if [[ "$CREATE_DIRS" =~ ^[Ss]$ ]]; then
        for p_path in "${PROJECT_PATHS[@]}"; do
            mkdir -p "$SCRIPT_DIR/$p_path" 2>/dev/null || true
            ok "Criado: $SCRIPT_DIR/$p_path"
        done
    fi
fi

# ============================================================
# 5. Criar refine-config.local.json se nao existir
# ============================================================
section "Refine Config Local"

if [[ -f "$LOCAL_CONFIG" ]]; then
    ok "refine-config.local.json ja existe"
    read -r -p "Recriar refine-config.local.json? (s/N): " RECREATE
else
    RECREATE="s"
fi

if [[ "$RECREATE" =~ ^[Ss]$ ]]; then
    if [[ -f "$LOCAL_CONFIG" ]]; then
        # Preservar projects do local config, atualizar apenas jira.baseUrl
        jq --arg base "$JIRA_BASE" \
           --argjson projects "$(jq '.projects' "$LOCAL_CONFIG")" \
           '.jira.baseUrl = $base | .projects = $projects' \
           "$CONFIG_FILE" > "$LOCAL_CONFIG"
    else
        jq --arg base "$JIRA_BASE" \
           '.jira.baseUrl = $base' "$CONFIG_FILE" > "$LOCAL_CONFIG"
    fi
    ok "refine-config.local.json criado/atualizado com JIRA_BASE=$JIRA_BASE"
fi

# ============================================================
# 6. Configurar ambiente shell
# ============================================================
section "Ambiente Shell"

RC_FILE="$HOME/.zshrc"
if [[ ! -f "$RC_FILE" ]]; then
    RC_FILE="$HOME/.bashrc"
fi

ENV_CHECK="reveal setup env"
if grep -q "$ENV_CHECK" "$RC_FILE" 2>/dev/null; then
    ok "Variaveis de ambiente ja configuradas em $RC_FILE"
else
    cat >> "$RC_FILE" << EOF

# === Reveal: $ENV_CHECK ===
export JIRA_USER="$JIRA_USER"
export JIRA_TOKEN="<token-salvo-em-~/.jira-credentials>"
export JIRA_BASE="$JIRA_BASE"
export ATLASSIAN_USER="$JIRA_USER"
export ATLASSIAN_TOKEN="<token-salvo-em-~/.jira-credentials>"
# === Fim Reveal ===
EOF
    ok "Variaveis de ambiente adicionadas ao $RC_FILE"
    warn "Token nao foi salvo em texto puro no $RC_FILE."
    warn "Edite $RC_FILE e substitua <token> pelo token real (ou use ~/.jira-credentials)"
fi

# ============================================================
# 7. Verificar hook de commit
# ============================================================
section "Pre-commit Hook"

HOOK_SOURCE="$SCRIPT_DIR/hooks/commit-msg"
HOOKS_DIR_PARENT=$(find "$SCRIPT_DIR/.." -maxdepth 2 -name ".git" -type d 2>/dev/null | head -1)

if [[ -n "$HOOKS_DIR_PARENT" ]]; then
    HOOK_DIR="${HOOKS_DIR_PARENT%/}/hooks"
    mkdir -p "$HOOK_DIR"
    if [[ -f "$HOOK_SOURCE" ]]; then
        cp "$HOOK_SOURCE" "$HOOK_DIR/commit-msg" 2>/dev/null || true
        chmod +x "$HOOK_DIR/commit-msg" 2>/dev/null || true
        ok "Pre-commit hook instalado em $HOOK_DIR/commit-msg"
    else
        warn "Hook nao encontrado em $HOOK_SOURCE"
    fi
else
    warn "Nenhum diretorio .git encontrado em projetos pais"
    warn "Pre-commit hook nao instalado (instale manualmente)"
fi

# ============================================================
# 8. Limpar diretorio vazio de ticket anterior
# ============================================================
section "Limpando artefatos anteriores"

if [[ -d "$SCRIPT_DIR/tickets/SPR-3417" ]] && [[ -z "$(ls -A "$SCRIPT_DIR/tickets/SPR-3417" 2>/dev/null)" ]]; then
    rmdir "$SCRIPT_DIR/tickets/SPR-3417" 2>/dev/null || true
    ok "Diretorio vazio tickets/SPR-3417 removido"
fi

# ============================================================
# 9. Gerar INDEX.md se não existir
# ============================================================
if [[ -f "$SCRIPT_DIR/generate-index.sh" ]]; then
    bash "$SCRIPT_DIR/generate-index.sh" 2>/dev/null || true
    ok "INDEX.md atualizado"
fi

# ============================================================
# Resumo Final
# ============================================================
section "Setup Concluido!"

echo ""
echo "  ✅ Dependencias: curl, jq, python3"
echo "  ✅ JIRA_BASE: $JIRA_BASE"
echo "  ✅ JIRA_USER: $JIRA_USER"
echo "  ✅ ~/.jira-credentials: criado"
echo "  ✅ refine-config.local.json: $( [[ -f "$LOCAL_CONFIG" ]] && echo 'criado' || echo 'ja existia' )"
echo ""
echo "  Para gerar a documentacao de um ticket:"
echo ""
echo "    ./refine-ticket.sh SPR-3417 --refine"
echo ""
echo "  Ou apenas o fetch Jira:"
echo ""
echo "    ./refine-ticket.sh SPR-3417 --jira-deep"
echo ""
echo "  Variaveis de ambiente configuradas nesta sessao:"
echo "    JIRA_USER, JIRA_TOKEN, JIRA_BASE, ATLASSIAN_USER, ATLASSIAN_TOKEN"
echo ""
