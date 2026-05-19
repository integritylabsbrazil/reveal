#!/bin/bash

# ============================================================
# code-scan.sh
# Modulo de analise de codigo — multi-linguagem e generico.
# Escaneia projetos, detecta linguagem, mapeia estrutura,
# e gera relatorio de impacto.
#
# Uso: source code-scan.sh && code_scan PROJECT_DIR [OUTPUT_FILE]
# ============================================================

set -euo pipefail

RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; BLUE='\033[34m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[SCAN]${NC} $1" >&2; }
log_ok()    { echo -e "${GREEN}[SCAN]${NC} $1" >&2; }
log_warn()  { echo -e "${YELLOW}[SCAN]${NC} $1" >&2; }
log_error() { echo -e "${RED}[SCAN]${NC} $1" >&2; }

# ============================================================
# Deteccao de linguagem e ferramentas
# ============================================================

detect_language() {
    local project_dir="$1"
    if [[ -f "$project_dir/settings.gradle" || -f "$project_dir/build.gradle" ]]; then
        echo "java:gradle"
    elif [[ -f "$project_dir/pom.xml" ]]; then
        echo "java:maven"
    elif [[ -f "$project_dir/package.json" ]]; then
        echo "javascript:npm"
    elif [[ -f "$project_dir/yarn.lock" ]]; then
        echo "javascript:yarn"
    elif [[ -f "$project_dir/requirements.txt" ]]; then
        echo "python:pip"
    elif [[ -f "$project_dir/pyproject.toml" ]]; then
        echo "python:poetry"
    elif [[ -f "$project_dir/go.mod" ]]; then
        echo "go:go"
    elif [[ -f "$project_dir/Cargo.toml" ]]; then
        echo "rust:cargo"
    elif [[ -f "$project_dir/Gemfile" ]]; then
        echo "ruby:bundler"
    else
        echo "unknown:unknown"
    fi
}

# ============================================================
# Mapeamento de estrutura
# ============================================================

scan_structure() {
    local project_dir="$1"
    local lang_tool
    lang_tool=$(detect_language "$project_dir")
    local lang="${lang_tool%%:*}"
    local tool="${lang_tool##*:}"

    echo "{"
    echo "  \"name\": \"$(basename "$project_dir")\","
    echo "  \"path\": \"$project_dir\","
    echo "  \"language\": \"$lang\","
    echo "  \"buildTool\": \"$tool\","

    # Submodulos (Gradle multi-module, Maven multi-module, npm workspaces)
    local modules_json
    modules_json=$(detect_modules "$project_dir" "$lang" "$tool")
    echo "  \"modules\": $modules_json,"

    # Pacotes/diretorios principais
    local packages_json
    packages_json=$(detect_packages "$project_dir" "$lang")
    echo "  \"packages\": $packages_json,"

    # Arquivos principais
    local files_json
    files_json=$(detect_key_files "$project_dir" "$lang")
    echo "  \"files\": $files_json"

    echo "}"
}

detect_modules() {
    local project_dir="$1"
    local lang="$2"
    local tool="$3"

    case "$lang/$tool" in
        java/gradle)
            if [[ -f "$project_dir/settings.gradle" ]]; then
                grep "^include " "$project_dir/settings.gradle" 2>/dev/null | \
                    sed "s/include //g; s/'//g; s/,//g" | \
                    jq -R -s 'split("\n") | map(select(length > 0) | {"name": ., "path": "\(.)"})' 2>/dev/null || echo "[]"
            else
                echo '[{"name": "(root)", "path": "."}]'
            fi
            ;;
        java/maven)
            if [[ -f "$project_dir/pom.xml" ]]; then
                python3 -c "
import xml.etree.ElementTree as ET
import sys
try:
    tree = ET.parse('$project_dir/pom.xml')
    root = tree.getroot()
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    modules = root.findall('.//m:module', ns)
    if modules:
        print([{'name': m.text.strip(), 'path': m.text.strip()} for m in modules])
    else:
        print('[{\"name\": \"(root)\", \"path\": \".\"}]')
except:
    print('[{\"name\": \"(root)\", \"path\": \".\"}]')
" 2>/dev/null || echo '[{"name": "(root)", "path": "."}]'
            else
                echo '[{"name": "(root)", "path": "."}]'
            fi
            ;;
        javascript/npm|javascript/yarn)
            if [[ -f "$project_dir/package.json" ]]; then
                python3 -c "
import json
try:
    with open('$project_dir/package.json') as f:
        data = json.load(f)
    workspaces = data.get('workspaces', [])
    if workspaces:
        print(json.dumps([{'name': w, 'path': w} for w in workspaces]))
    else:
        print('[{\"name\": \"(root)\", \"path\": \".\"}]')
except:
    print('[{\"name\": \"(root)\", \"path\": \".\"}]')
" 2>/dev/null || echo '[{"name": "(root)", "path": "."}]'
            else
                echo '[{"name": "(root)", "path": "."}]'
            fi
            ;;
        *)
            echo '[{"name": "(root)", "path": "."}]'
            ;;
    esac
}

detect_packages() {
    local project_dir="$1"
    local lang="$2"

    case "$lang" in
        java)
            # Encontrar diretorios com arquivos .java (pacotes)
            local src_dirs
            src_dirs=$(find "$project_dir/src/main/java" -type d 2>/dev/null || true)
            if [[ -z "$src_dirs" ]]; then
                src_dirs=$(find "$project_dir/src" -type d 2>/dev/null || true)
            fi
            if [[ -n "$src_dirs" ]]; then
                echo "$src_dirs" | \
                    sed "s|$project_dir/src/main/java/||;s|$project_dir/src/||" | \
                    grep -v '^$' | \
                    sort -u | \
                    jq -R -s 'split("\n") | map(select(length > 0) | gsub("/"; "."))' 2>/dev/null || echo "[]"
            else
                echo "[]"
            fi
            ;;
        javascript|python|go|rust|ruby)
            local src_dirs
            src_dirs=$(find "$project_dir/src" -type d -maxdepth 4 2>/dev/null || true)
            if [[ -z "$src_dirs" ]]; then
                src_dirs=$(find "$project_dir" -type d -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/build/*" -not -path "*/target/*" -maxdepth 3 2>/dev/null || true)
            fi
            if [[ -n "$src_dirs" ]]; then
                echo "$src_dirs" | \
                    sed "s|$project_dir/||" | \
                    grep -v '^$' | grep -v '^\..' | \
                    sort -u | \
                    jq -R -s 'split("\n") | map(select(length > 0))' 2>/dev/null || echo "[]"
            else
                echo "[]"
            fi
            ;;
        *)
            echo "[]"
            ;;
    esac
}

detect_key_files() {
    local project_dir="$1"
    local lang="$2"

    local files_json="[]"

    case "$lang" in
        java)
            # Encontrar endpoints, controllers, services, delegates (padroes comuns)
            local endpoints
            endpoints=$(find "$project_dir/src" -name "*Endpoint.java" -o -name "*Controller.java" -o -name "*Client.java" -o -name "*Service.java" -o -name "*Delegate.java" 2>/dev/null | head -30 || true)
            if [[ -n "$endpoints" ]]; then
                files_json=$(echo "$endpoints" | while IFS= read -r f; do
                    rel_path="${f#$project_dir/}"
                    ftype="other"
                    basename "$f" | grep -qi "endpoint" && ftype="endpoint"
                    basename "$f" | grep -qi "controller" && ftype="controller"
                    basename "$f" | grep -qi "client" && ftype="client"
                    basename "$f" | grep -qi "service" && ftype="service"
                    basename "$f" | grep -qi "delegate" && ftype="delegate"
                    echo "{\"path\": \"$rel_path\", \"type\": \"$ftype\"}"
                done | jq -s '.')
            fi
            ;;
        javascript|typescript)
            local api_files
            api_files=$(find "$project_dir/src" -name "*.api.*" -o -name "*.route.*" -o -name "*.controller.*" -o -name "*.service.*" -o -name "index.ts" -o -name "index.js" 2>/dev/null | head -30 || true)
            if [[ -n "$api_files" ]]; then
                files_json=$(echo "$api_files" | while IFS= read -r f; do
                    rel_path="${f#$project_dir/}"
                    echo "{\"path\": \"$rel_path\", \"type\": \"module\"}"
                done | jq -s '.')
            fi
            ;;
        python)
            local py_files
            py_files=$(find "$project_dir/src" -name "*.py" 2>/dev/null | head -30 || true)
            if [[ -n "$py_files" ]]; then
                files_json=$(echo "$py_files" | while IFS= read -r f; do
                    rel_path="${f#$project_dir/}"
                    echo "{\"path\": \"$rel_path\", \"type\": \"module\"}"
                done | jq -s '.')
            fi
            ;;
    esac

    echo "$files_json"
}

# ============================================================
# Busca de implementacoes similares
# ============================================================

find_similar_tickets() {
    local tickets_dir="$1"
    local component="$2"

    if [[ ! -d "$tickets_dir" ]]; then
        echo "[]"
        return 0
    fi

    local results="[]"
    for ticket_dir in "$tickets_dir"/[A-Z]*-[0-9]*/; do
        if [[ ! -d "$ticket_dir" ]]; then
            continue
        fi
        local ticket_id
        ticket_id=$(basename "$ticket_dir")

        # Pular o proprio ticket (se estiver sendo analisado)
        if [[ -n "${TICKET_ID:-}" && "$ticket_id" == "$TICKET_ID" ]]; then
            continue
        fi

        local json_file="$ticket_dir/jira-data.json"
        if [[ -f "$json_file" ]]; then
            if command -v jq &> /dev/null; then
                local summary
                summary=$(jq -r '.summary // .basic.summary // ""' "$json_file" 2>/dev/null || true)
                local components_json
                components_json=$(jq -c '.components // .basic.components // []' "$json_file" 2>/dev/null || echo "[]")
                if echo "$components_json" | grep -qi "$component" 2>/dev/null; then
                    results=$(echo "$results" | jq -c --arg id "$ticket_id" --arg s "$summary" '. + [{"ticketId": $id, "summary": $s}]')
                fi
            fi
        fi
    done

    echo "$results"
}

# ============================================================
# Scan principal
# ============================================================

code_scan() {
    local project_dir="$1"
    local output_file="${2:-}"

    if [[ ! -d "$project_dir" ]]; then
        log_error "Diretorio nao encontrado: $project_dir"
        return 1
    fi

    project_dir=$(cd "$project_dir" && pwd)
    log_info "Escaneando: $project_dir"

    local lang_tool
    lang_tool=$(detect_language "$project_dir")
    local lang="${lang_tool%%:*}"
    local tool="${lang_tool##*:}"

    log_info "Linguagem detectada: $lang ($tool)"

    local structure
    structure=$(scan_structure "$project_dir")

    if [[ -n "$output_file" ]]; then
        echo "$structure" > "$output_file"
        log_ok "Relatorio salvo em $output_file"
    fi

    echo "$structure"
    return 0
}

# ============================================================
# Gera resumo markdown legivel
# ============================================================

code_scan_summary() {
    local scan_json="$1"

    local name
    name=$(echo "$scan_json" | jq -r '.name // "unknown"')
    local lang
    lang=$(echo "$scan_json" | jq -r '.language // "unknown"')
    local tool
    tool=$(echo "$scan_json" | jq -r '.buildTool // "unknown"')

    echo "### Projeto: $name"
    echo ""
    echo "| Atributo | Valor |"
    echo "|----------|-------|"
    echo "| **Linguagem** | $lang |"
    echo "| **Build Tool** | $tool |"
    echo ""

    local modules
    modules=$(echo "$scan_json" | jq -c '.modules // []')
    local module_count
    module_count=$(echo "$modules" | jq 'length')
    if [[ "$module_count" -gt 0 && "$module_count" -le 20 ]]; then
        echo "**Modulos:**"
        echo "$modules" | jq -r '.[] | "- \(.name)"'
        echo ""
    fi

    local packages
    packages=$(echo "$scan_json" | jq -c '.packages // []')
    local pkg_count
    pkg_count=$(echo "$packages" | jq 'length')
    if [[ "$pkg_count" -gt 0 && "$pkg_count" -le 30 ]]; then
        echo "**Pacotes/Diretorios:**"
        echo "$packages" | jq -r '.[:20][] | "- \(.)"'
        if [[ "$pkg_count" -gt 20 ]]; then
            echo "  ... e mais $((pkg_count - 20)) pacotes"
        fi
        echo ""
    fi

    local files
    files=$(echo "$scan_json" | jq -c '.files // []')
    local file_count
    file_count=$(echo "$files" | jq 'length')
    if [[ "$file_count" -gt 0 ]]; then
        echo "**Arquivos relevantes:**"
        echo "$files" | jq -r '.[] | "- \(.type): \(.path)"'
        echo ""
    fi
}

# ============================================================
# Execucao direta
# ============================================================
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 1 ]]; then
        echo "Uso: $0 PROJETO_DIR [OUTPUT_JSON]"
        echo ""
        echo "Escaneia a estrutura do projeto e gera relatorio JSON."
        echo ""
        echo "Exemplos:"
        echo "  $0 ../projetos/meu-app"
        echo "  $0 ../projetos/meu-app ./tmp/scan-report.json"
        exit 1
    fi
    code_scan "$@"
fi
