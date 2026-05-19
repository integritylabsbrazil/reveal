#!/bin/bash

# ============================================================
# refine-ticket.sh
# Ferramenta generica de refinamento tecnico.
# Conecta-se a qualquer Jira, escaneia qualquer base de codigo,
# gera perguntas para o negocio e documento de refinamento.
#
# Uso: ./refine-ticket.sh TICKET_ID [opcoes]
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
TEMPLATES_DIR="$SCRIPT_DIR/templates"
TICKETS_DIR="$SCRIPT_DIR/tickets"
CONFIG_FILE="$SCRIPT_DIR/refine-config.json"
LOCAL_CONFIG="$SCRIPT_DIR/refine-config.local.json"

RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; BLUE='\033[34m'; CYAN='\033[36m'; NC='\033[0m'

# ============================================================
# Utilitarios
# ============================================================

log_info()    { echo -e "${BLUE}[REFINE]${NC} $1"; }
log_ok()      { echo -e "${GREEN}[REFINE]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[REFINE]${NC} $1"; }
log_error()   { echo -e "${RED}[REFINE]${NC} $1"; }
log_section() { echo ""; echo -e "${CYAN}═══════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}═══════════════════════════════════════${NC}"; echo ""; }

usage() {
    cat <<EOF
Uso: $0 TICKET_ID [opcoes]

Ferramenta generica de refinamento tecnico.
Conecta-se a qualquer Jira, escaneia codigo fonte e gera
documentos de refinamento completos.

Opcoes:
  --refine               Pipeline completo: fetch → scan → questions → refine
  --jira-deep            Apenas deep fetch Jira (epico, links, subtasks, comentarios)
  --scan-impact          Apenas scan de codigo
  --questions            Apenas geracao de perguntas para o negocio
  --refinement           Apenas geracao do documento de refinamento tecnico
  --all                  Executa todas as etapas (equivalente a --refine)

  --config FILE          Arquivo de configuracao (default: refine-config.json)
  --jira-base URL        URL base do Jira (ex: https://meujira.atlassian.net)
  --project-dir DIR      Diretorio do projeto para code scan
  --help, -h             Exibir esta ajuda

Variaveis de ambiente:
  JIRA_USER              Email ou usuario Jira
  JIRA_TOKEN             Token de API do Jira
  JIRA_BASE              URL base do Jira (alternativa a --jira-base)

Exemplos:
  $0 PROJ-123 --refine
  $0 PROJ-123 --jira-deep
  $0 PROJ-456 --scan-impact
  $0 PROJ-123 --config ./meu-config.json --refine
EOF
    exit 0
}

# ============================================================
# Parse de argumentos
# ============================================================

TICKET_ID=""
MODE=""
LOADED_CONFIG_FILE="$CONFIG_FILE"

if [[ $# -eq 0 ]]; then
    usage
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --refine|--all|-a)
            MODE="refine"
            shift
            ;;
        --jira-deep|-j)
            MODE="jira-deep"
            shift
            ;;
        --scan-impact|-s)
            MODE="scan-impact"
            shift
            ;;
        --questions|-q)
            MODE="questions"
            shift
            ;;
        --refinement|-r)
            MODE="refinement"
            shift
            ;;
        --config|-c)
            if [[ $# -lt 2 ]]; then
                echo "Erro: --config requer um argumento"
                exit 1
            fi
            LOADED_CONFIG_FILE="$2"
            shift 2
            ;;
        --jira-base|-b)
            if [[ $# -lt 2 ]]; then
                echo "Erro: --jira-base requer um argumento"
                exit 1
            fi
            JIRA_BASE="$2"
            shift 2
            ;;
        --project-dir|-p)
            if [[ $# -lt 2 ]]; then
                echo "Erro: --project-dir requer um argumento"
                exit 1
            fi
            PROJECT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        *)
            if [[ -z "$TICKET_ID" ]]; then
                TICKET_ID="$1"
                if [[ -z "$MODE" ]]; then
                    MODE="refine"
                fi
            else
                echo "Erro: argumento desconhecido: $1"
                usage
            fi
            shift
            ;;
    esac
done

if [[ -z "$TICKET_ID" ]]; then
    echo "Erro: TICKET_ID e obrigatorio"
    usage
fi

# ============================================================
# Carregar configuracao
# ============================================================

load_config() {
    local config_file="$1"

    # Priorizar refine-config.local.json se existir
    if [[ -f "$LOCAL_CONFIG" ]]; then
        config_file="$LOCAL_CONFIG"
    fi

    if [[ -f "$config_file" ]]; then
        log_info "Carregando configuracao: $config_file"

        # Jira base
        local jira_base
        jira_base=$(jq -r '.jira.baseUrl // ""' "$config_file" 2>/dev/null || true)
        if [[ -n "$jira_base" && -z "${JIRA_BASE:-}" ]]; then
            JIRA_BASE="$jira_base"
        fi

        # Projetos
        if [[ -z "${PROJECT_DIR:-}" ]]; then
            local projects
            projects=$(jq -r '.projects[0].path // ""' "$config_file" 2>/dev/null || true)
            if [[ -n "$projects" && "$projects" != '""' ]]; then
                # Resolver caminho relativo ao diretorio do config
                local config_dir
                config_dir=$(cd "$(dirname "$config_file")" && pwd)
                PROJECT_DIR=$(cd "$config_dir/$projects" 2>/dev/null && pwd || echo "$config_dir/$projects")
            fi
        fi
    else
        log_warn "Arquivo de configuracao nao encontrado: $config_file"
        log_warn "Use variaveis de ambiente ou parametros diretos."
    fi
}

load_config "$LOADED_CONFIG_FILE"

# ============================================================
# Verificar dependencias
# ============================================================

check_deps() {
    local missing=0
    for cmd in curl jq python3; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Dependencia faltando: $cmd"
            missing=1
        fi
    done
    if [[ "$missing" -eq 1 ]]; then
        echo ""
        echo "Instale as dependencias:"
        echo "  sudo apt-get install curl jq python3"
        exit 1
    fi
}

# ============================================================
# Modulos
# ============================================================

source_module() {
    local module="$1"
    local module_path="$LIB_DIR/$module"
    if [[ ! -f "$module_path" ]]; then
        log_error "Modulo nao encontrado: $module_path"
        exit 1
    fi
    source "$module_path"
}

# ============================================================
# Pipeline: Jira Deep Fetch
# ============================================================

run_jira_deep() {
    log_section "Deep Fetch Jira"
    source_module "jira-fetch.sh"
    jira_deep_fetch "$TICKET_ID" "$TICKET_DIR"
}

# ============================================================
# Pipeline: Code Scan
# ============================================================

run_code_scan() {
    log_section "Code Impact Scan"

    if [[ -z "${PROJECT_DIR:-}" ]]; then
        log_warn "Nenhum diretorio de projeto configurado."
        log_warn "Use --project-dir ou configure refine-config.json"
        log_warn "Pulando code scan..."
        return 0
    fi

    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_warn "Diretorio do projeto nao encontrado: $PROJECT_DIR"
        log_warn "Pulando code scan..."
        return 0
    fi

    source_module "code-scan.sh"
    local scan_output="$TICKET_DIR/impact-report.json"

    # Se for multi-module, escanear submodulos
    local lang_tool
    lang_tool=$(detect_language "$PROJECT_DIR")
    local lang="${lang_tool%%:*}"

    if [[ "$lang" == "java" && -f "$PROJECT_DIR/settings.gradle" ]]; then
        local modules
        modules=$(grep "^include " "$PROJECT_DIR/settings.gradle" 2>/dev/null || true)
        if [[ -n "$modules" ]]; then
            log_info "Projeto multi-module detectado. Escaneando todos os modulos..."
            local all_scans=""
            local first=true
            local mod_list
            mod_list=$(echo "$modules" | sed "s/include //g; s/'//g; s/,//g")
            while IFS= read -r mod; do
                mod=$(echo "$mod" | xargs)
                [[ -z "$mod" ]] && continue
                local mod_dir="$PROJECT_DIR/$mod"
                if [[ -d "$mod_dir" ]]; then
                    local mod_scan
                    mod_scan=$(code_scan "$mod_dir")
                    if [[ "$first" == true ]]; then
                        all_scans="${mod_scan}"
                        first=false
                    else
                        all_scans="${all_scans},${mod_scan}"
                    fi
                fi
            done <<< "$mod_list"
            echo "[${all_scans}]" > "$scan_output"
            log_ok "Scan multi-module salvo em $scan_output"
        fi
    else
        code_scan "$PROJECT_DIR" "$scan_output"
    fi
}

# ============================================================
# Pipeline: Generate Questions
# ============================================================

run_questions() {
    log_section "Gerando Perguntas para o Negocio"

    if [[ ! -f "$TICKET_DIR/jira-data.json" ]]; then
        log_warn "jira-data.json nao encontrado. Execute --jira-deep primeiro."
        log_warn "Pulando geracao de perguntas..."
        return 0
    fi

    source_module "generate-questions.sh"
    generate_questions "$TICKET_DIR"
}

# ============================================================
# Pipeline: Generate Refinement
# ============================================================

run_refinement() {
    log_section "Gerando Refinamento Tecnico"

    if [[ ! -f "$TICKET_DIR/jira-data.json" ]]; then
        log_error "jira-data.json nao encontrado. Execute --jira-deep primeiro."
        return 1
    fi

    source_module "generate-refinement.sh"
    generate_refinement "$TICKET_DIR"
}

# ============================================================
# Main
# ============================================================

main() {
    check_deps

    TICKET_DIR="$TICKETS_DIR/$TICKET_ID"
    mkdir -p "$TICKET_DIR"

    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       REFINE TICKET — Refinamento Tecnico       ║${NC}"
    echo -e "${CYAN}║       Ticket: $TICKET_ID${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ -n "${JIRA_BASE:-}" ]]; then
        echo "  Jira base: $JIRA_BASE"
    fi
    if [[ -n "${PROJECT_DIR:-}" ]]; then
        echo "  Projeto: $PROJECT_DIR"
    fi
    echo "  Diretorio: $TICKET_DIR"
    echo ""

    case "$MODE" in
        jira-deep)
            run_jira_deep
            ;;
        scan-impact)
            run_code_scan
            ;;
        questions)
            run_jira_deep 2>/dev/null || true
            run_questions
            ;;
        refinement)
            run_refinement
            ;;
        refine|*)
            run_jira_deep
            run_code_scan
            run_questions
            run_refinement
            ;;
    esac

    # Resumo final
    echo ""
    log_section "Resumo"
    echo ""
    echo "  Ticket: $TICKET_ID"
    echo "  Diretorio: $TICKET_DIR"
    echo "  Arquivos gerados:"
    [[ -f "$TICKET_DIR/jira-data.json" ]]          && echo "    ✅ jira-data.json (dados completos Jira)"
    [[ -f "$TICKET_DIR/jira-summary.md" ]]          && echo "    ✅ jira-summary.md (resumo Jira)"
    [[ -f "$TICKET_DIR/impact-report.json" ]]       && echo "    ✅ impact-report.json (scan de codigo)"
    [[ -f "$TICKET_DIR/perguntas-negocio.md" ]]     && echo "    ✅ perguntas-negocio.md (perguntas p/ negocio)"
    [[ -f "$TICKET_DIR/perguntas-negocio.json" ]]   && echo "    ✅ perguntas-negocio.json (perguntas em JSON)"
    [[ -f "$TICKET_DIR/refinamento-tecnico.md" ]]   && echo "    ✅ refinamento-tecnico.md (documento completo)"
    echo ""
    echo -e "${GREEN}Refinamento concluido!${NC}"
    echo ""
    echo "Proximos passos sugeridos:"
    echo "  1. Enviar perguntas-negocio.md para o PO/analista de negocio"
    echo "  2. Apos respostas, refinar implementation-plan.md"
    echo "  3. Gerar subtarefas em status-tasks.json"
    echo "  4. Iniciar implementacao seguindo o AGENTS.md"
    echo ""
}

main
