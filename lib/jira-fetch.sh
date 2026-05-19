#!/bin/bash

# ============================================================
# jira-fetch.sh
# Modulo de deep fetch Jira — generico para qualquer instancia.
# Busca dados completos do ticket: epico, links, subtasks,
# comentarios, changelog, anexos.
#
# Uso: source jira-fetch.sh && jira_deep_fetch TICKET_ID [OUTPUT_DIR]
# ============================================================

set -euo pipefail

JIRA_BASE="${JIRA_BASE:-https://seudominio.atlassian.net}"
JIRA_API_VERSION="${JIRA_API_VERSION:-3}"
JIRA_AGILE_VERSION="${JIRA_AGILE_VERSION:-1.0}"

# Cores
RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; BLUE='\033[34m'; NC='\033[0m'

# ============================================================
# Utilitarios
# ============================================================

log_info()  { echo -e "${BLUE}[JIRA]${NC} $1" >&2; }
log_ok()    { echo -e "${GREEN}[JIRA]${NC} $1" >&2; }
log_warn()  { echo -e "${YELLOW}[JIRA]${NC} $1" >&2; }
log_error() { echo -e "${RED}[JIRA]${NC} $1" >&2; }

load_credentials() {
    if [[ -n "${JIRA_USER:-}" && -n "${JIRA_TOKEN:-}" ]]; then
        return 0
    fi
    if [[ -f "$HOME/.jira-credentials" ]]; then
        IFS=':' read -r JIRA_USER JIRA_TOKEN < "$HOME/.jira-credentials"
        return 0
    fi
    log_error "Credenciais Jira nao encontradas."
    echo "  Configure JIRA_USER + JIRA_TOKEN como env vars"
    echo "  Ou crie ~/.jira-credentials (formato: usuario:token)"
    return 1
}

jira_api_get() {
    local path="$1"
    local url="${JIRA_BASE}${path}"
    local response_file
    response_file=$(mktemp)
    local http_code
    http_code=$(curl -s -w "%{http_code}" -o "$response_file" \
        -u "$JIRA_USER:$JIRA_TOKEN" \
        -H "Accept: application/json" \
        "$url" || echo "000")
    if [[ "$http_code" != "200" && "$http_code" != "201" ]]; then
        log_warn "HTTP $http_code em $path"
        rm -f "$response_file"
        return 1
    fi
    cat "$response_file"
    rm -f "$response_file"
    return 0
}

jira_api_get_paginated() {
    local base_path="$1"
    local max_results="${2:-100}"
    local start_at=0
    local total=0
    local all_items="[]"
    local first=true

    while true; do
        local base="${base_path%%\?*}"
        local sep="?"
        [[ "$base_path" == *\?* ]] && sep="&"
        local path="${base}${sep}startAt=${start_at}&maxResults=${max_results}"
        local response
        response=$(jira_api_get "$path") || return 1
        if [[ -z "$response" ]]; then
            break
        fi

        local items
        items=$(echo "$response" | jq -c '.values // .issues // .comments // []')
        if [[ "$first" == true ]]; then
            total=$(echo "$response" | jq -r '.total // 0')
            first=false
        fi

        all_items=$(echo "$all_items" | jq -c --argjson items "$items" '. + $items')
        start_at=$((start_at + max_results))
        if [[ "$start_at" -ge "$total" ]]; then
            break
        fi
    done

    echo "$all_items"
}

# ============================================================
# Deep Fetch Principal
# ============================================================

jira_deep_fetch() {
    local ticket_id="$1"
    local output_dir="${2:-.}"

    load_credentials || return 1
    export JIRA_USER JIRA_TOKEN

    log_info "Iniciando deep fetch de $ticket_id"

    # Diretorio temporario para arquivos intermediarios
    local tmp_dir
    tmp_dir=$(mktemp -d)

    # 1. Dados basicos do ticket
    log_info "Buscando dados basicos..."
    local basic_data
    basic_data=$(jira_api_get "/rest/api/${JIRA_API_VERSION}/issue/${ticket_id}?expand=renderedFields,changelog,names,schema") || {
        local http_code
        http_code=$(curl -s -o /dev/null -w "%{http_code}" -u "$JIRA_USER:$JIRA_TOKEN" \
            "${JIRA_BASE}/rest/api/${JIRA_API_VERSION}/issue/${ticket_id}" 2>/dev/null || echo "000")
        log_error "Falha ao buscar ticket $ticket_id (HTTP $http_code)"
        case "$http_code" in
            401|403) log_warn "  Possivel causa: Token expirado ou invalido. Regere em https://id.atlassian.com/manage/api-tokens" ;;
            404)     log_warn "  Possivel causa: Ticket '$ticket_id' nao existe ou projeto errado. Verifique o ID." ;;
            000)     log_warn "  Possivel causa: URL base '$JIRA_BASE' inacessivel ou credenciais incorretas." ;;
        esac
        return 1
    }
    log_ok "Dados basicos obtidos"

    # 2. Extrair epico pai
    local parent_key=""
    local parent_summary=""
    local parent_epic_data=""
    parent_key=$(echo "$basic_data" | jq -r '.fields.parent.key // .fields.customfield_10067 // ""')
    if [[ -n "$parent_key" && "$parent_key" != "null" ]]; then
        log_info "Buscando epico pai: $parent_key..."
        parent_epic_data=$(jira_api_get "/rest/api/${JIRA_API_VERSION}/issue/${parent_key}?fields=summary,status,priority,issuetype,customfield_10005,description") || log_warn "Nao foi possivel buscar epico $parent_key"
        if [[ -n "$parent_epic_data" ]]; then
            parent_summary=$(echo "$parent_epic_data" | jq -r '.fields.summary // ""')
            log_ok "Epico pai: $parent_key - $parent_summary"
        fi
    fi

    # 3. Issues vinculadas (issuelinks)
    log_info "Buscando issues vinculadas..."
    local linked_issues="[]"
    linked_issues=$(echo "$basic_data" | jq -c '[.fields.issuelinks[]? | {
        id: .id,
        type: (.type.name // .type.outwardName // "relates"),
        inward: .inwardIssue.key // null,
        outward: .outwardIssue.key // null,
        direction: (if .inwardIssue then "inward" else "outward" end),
        summary: (.inwardIssue.fields.summary // .outwardIssue.fields.summary // null),
        status: (.inwardIssue.fields.status.name // .outwardIssue.fields.status.name // null)
    }]')
    local link_count
    link_count=$(echo "$linked_issues" | jq 'length')
    log_ok "Issues vinculadas: $link_count"

    # 4. Subtasks
    log_info "Buscando subtasks..."
    local subtasks="[]"
    subtasks=$(echo "$basic_data" | jq -c '[.fields.subtasks[]? | {
        key: .key,
        summary: .fields.summary,
        status: .fields.status.name,
        assignee: .fields.assignee.displayName // null,
        priority: .fields.priority.name // null
    }]')
    local sub_count
    sub_count=$(echo "$subtasks" | jq 'length')
    log_ok "Subtasks: $sub_count"

    # 5. Comentarios (ultimos 50)
    log_info "Buscando comentarios..."
    local comments="[]"
    comments=$(jira_api_get_paginated "/rest/api/${JIRA_API_VERSION}/issue/${ticket_id}/comment" 50) || log_warn "Nao foi possivel buscar comentarios"
    local comment_count=0
    if echo "$comments" | jq -e '. | length > 0' > /dev/null 2>&1; then
        comments=$(echo "$comments" | jq -c '[.[] | {
            id: .id,
            author: .author.displayName // "unknown",
            body: (.body | if type == "object" then [.. | objects | select(.type == "text") | .text] | join("\n") else . end),
            created: .created,
            updated: .updated
        }]')
        comment_count=$(echo "$comments" | jq 'length')
    fi
    log_ok "Comentarios: $comment_count"

    # 6. Changelog (historico de transicoes)
    log_info "Buscando changelog..."
    local changelog="[]"
    changelog=$(echo "$basic_data" | jq -c '[.changelog.histories[]? | {
        id: .id,
        author: .author.displayName // "unknown",
        created: .created,
        items: [.items[]? | {
            field: .field,
            fromString: .fromString,
            toString: .toString
        }]
    }]')
    local changelog_count
    changelog_count=$(echo "$changelog" | jq 'length')
    log_ok "Changelog entries: $changelog_count"

    # 7. Anexos
    log_info "Buscando anexos..."
    local attachments="[]"
    attachments=$(echo "$basic_data" | jq -c '[.fields.attachment[]? | {
        id: .id,
        filename: .filename,
        mimeType: .mimeType,
        size: .size,
        author: .author.displayName // "unknown",
        created: .created,
        contentUrl: .content
    }]')
    local attach_count
    attach_count=$(echo "$attachments" | jq 'length')
    log_ok "Anexos: $attach_count"

    # 7.5. Download de anexos (com dedup por MD5)
    local attach_dir="$output_dir/attachments"
    local updated_attachments
    updated_attachments=$(echo "$attachments" | python3 -c "
import sys, json, hashlib, os, subprocess

data = json.load(sys.stdin)
if not data:
    print(json.dumps(data))
    sys.exit(0)

attach_dir = os.path.join('$attach_dir')
os.makedirs(attach_dir, exist_ok=True)

# Track already-seen MD5s to avoid duplicates
seen_md5 = {}
result = []

for att in data:
    entry = dict(att)
    content_url = att.get('contentUrl', '')
    filename = att.get('filename', 'unknown')
    
    if not content_url:
        entry['downloadedPath'] = None
        entry['downloadError'] = 'no contentUrl'
        result.append(entry)
        continue
    
    # Download to temp
    tmp = os.path.join(attach_dir, '.tmp_' + filename)
    try:
        # Use curl with auth from env
        env = os.environ.copy()
        user = env.get('JIRA_USER', '')
        token = env.get('JIRA_TOKEN', '')
        subprocess.run(
            ['curl', '-sL', '-o', tmp, '-u', f'{user}:{token}', content_url],
            check=True, capture_output=True, timeout=30
        )
    except Exception as e:
        entry['downloadedPath'] = None
        entry['downloadError'] = str(e)
        result.append(entry)
        continue
    
    # Calculate MD5
    md5 = hashlib.md5()
    with open(tmp, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            md5.update(chunk)
    md5_hex = md5.hexdigest()
    
    # Dedup: check if we already have this file
    if md5_hex in seen_md5:
        os.remove(tmp)
        entry['downloadedPath'] = seen_md5[md5_hex]
        entry['md5'] = md5_hex
        result.append(entry)
        continue
    
    # Unique file: move to final name
    final_path = os.path.join(attach_dir, filename)
    # Handle name collision
    counter = 1
    while os.path.exists(final_path):
        name, ext = os.path.splitext(filename)
        final_path = os.path.join(attach_dir, f'{name}_{counter}{ext}')
        counter += 1
    
    os.rename(tmp, final_path)
    seen_md5[md5_hex] = final_path
    entry['downloadedPath'] = final_path
    entry['md5'] = md5_hex
    result.append(entry)

print(json.dumps(result))
") || attachments="$attachments"  # fallback: keep original if python fails

    # Save updated attachments back to temp file
    if [[ -n "$updated_attachments" && "$updated_attachments" != "null" ]]; then
        attachments="$updated_attachments"
        echo "$attachments" > "$tmp_dir/attachments.json"
        local unique_count
        unique_count=$(echo "$attachments" | python3 -c "
import sys, json
data = json.load(sys.stdin)
seen = set()
for att in data:
    p = att.get('downloadedPath')
    if p:
        seen.add(p)
print(len(seen))
" 2>/dev/null || echo "?")
        log_ok "Anexos baixados: $unique_count arquivos unicos em $attach_dir"
    fi

    # 8. Dados ageis (sprint, story points) via API Agile
    log_info "Buscando dados ageis..."
    local agile_data="{}"
    local agile_response
    agile_response=$(jira_api_get "/rest/agile/${JIRA_AGILE_VERSION}/issue/${ticket_id}") || agile_response=""
    if [[ -n "$agile_response" ]]; then
        agile_data=$(echo "$agile_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
except Exception:
    print('{\"sprint\": null, \"storyPoints\": null, \"epic\": null}')
    sys.exit(0)
fields = data.get('fields', {})
print(json.dumps({
    'sprint': fields.get('sprint') or fields.get('customfield_10007'),
    'storyPoints': fields.get('storyPoints') or fields.get('customfield_10004'),
    'epic': fields.get('epic')
}))
" 2>/dev/null || echo '{"sprint":null,"storyPoints":null,"epic":null}')
    fi
    log_ok "Dados ageis obtidos"

    # 9. Salvar dados em arquivos temporarios para evitar limites de ARG_MAX
    echo "$basic_data" > "$tmp_dir/basic.json"
    echo "${parent_epic_data:-null}" > "$tmp_dir/epic.json"
    echo "${linked_issues:-[]}" > "$tmp_dir/linked.json"
    echo "${subtasks:-[]}" > "$tmp_dir/subtasks.json"
    echo "${comments:-[]}" > "$tmp_dir/comments.json"
    echo "${changelog:-[]}" > "$tmp_dir/changelog.json"
    echo "${attachments:-[]}" > "$tmp_dir/attachments.json"
    echo "${agile_data:-{}}" > "$tmp_dir/agile.json"

    local lib_dir
    lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local full_data
    full_data=$(python3 "$lib_dir/assemble_jira.py" \
        "$ticket_id" "$tmp_dir")

    rm -rf "$tmp_dir"

    # 10. Salvar
    mkdir -p "$output_dir"
    local output_file="$output_dir/jira-data.json"
    echo "$full_data" > "$output_file"
    log_ok "Dados completos salvos em $output_file"

    # 11. Gerar resumo markdown
    local summary_file="$output_dir/jira-summary.md"
    {
        echo "# $ticket_id: $(echo "$full_data" | jq -r '.basic.summary')"
        echo ""
        echo "| Campo | Valor |"
        echo "|-------|-------|"
        echo "| **Status** | $(echo "$full_data" | jq -r '.basic.status') |"
        echo "| **Prioridade** | $(echo "$full_data" | jq -r '.basic.priority') |"
        echo "| **Tipo** | $(echo "$full_data" | jq -r '.basic.issuetype') |"
        echo "| **Responsavel** | $(echo "$full_data" | jq -r '.basic.assignee // "—"') |"
        echo "| **Solicitante** | $(echo "$full_data" | jq -r '.basic.reporter // "—"') |"
        echo "| **Criado em** | $(echo "$full_data" | jq -r '.basic.created') |"
        echo "| **Atualizado em** | $(echo "$full_data" | jq -r '.basic.updated') |"
        echo ""
        echo "## Descricao"
        echo ""
        local desc_html
        desc_html=$(echo "$full_data" | jq -r '.basic.descriptionRendered // .basic.description // "*Sem descricao*"')
        echo "$desc_html" | sed 's/<[^>]*>//g' | sed '/^$/N;/^\n$/D'
        echo ""

        # Campos personalizados
        local custom_fields
        custom_fields=$(echo "$full_data" | jq -r '.customFields | to_entries[] | "| \(.value.name) | \(.value.value) |"' 2>/dev/null || true)
        if [[ -n "$custom_fields" ]]; then
            echo "## Campos Personalizados"
            echo ""
            echo "| Campo | Valor |"
            echo "|-------|-------|"
            echo "$custom_fields"
            echo ""
        fi

        local epic_key
        epic_key=$(echo "$full_data" | jq -r '.epic.key // ""')
        if [[ -n "$epic_key" && "$epic_key" != "null" ]]; then
            echo "## Epico"
            echo ""
            echo "| Campo | Valor |"
            echo "|-------|-------|"
            echo "| **Chave** | [$epic_key](${JIRA_BASE}/browse/$epic_key) |"
            echo "| **Resumo** | $(echo "$full_data" | jq -r '.epic.summary') |"
            echo "| **Status** | $(echo "$full_data" | jq -r '.epic.status') |"
            echo ""
        fi

        local link_len
        link_len=$(echo "$full_data" | jq '.linkedIssues | length')
        if [[ "$link_len" -gt 0 ]]; then
            echo "## Issues Vinculadas"
            echo ""
            echo "| Tipo | Issue | Resumo | Status |"
            echo "|------|-------|--------|--------|"
            echo "$full_data" | jq -r '.linkedIssues[] | "| \(.type) | [\(.inward // .outward)](\(env.JIRA_BASE)/browse/\(.inward // .outward)) | \(.summary // "—") | \(.status // "—") |"'
            echo ""
        fi

        local sub_len
        sub_len=$(echo "$full_data" | jq '.subtasks | length')
        if [[ "$sub_len" -gt 0 ]]; then
            echo "## Subtasks"
            echo ""
            echo "| Issue | Resumo | Status |"
            echo "|-------|--------|--------|"
            echo "$full_data" | jq -r '.subtasks[] | "| [\(.key)](\(env.JIRA_BASE)/browse/\(.key)) | \(.summary) | \(.status) |"'
            echo ""
        fi

        local comm_len
        comm_len=$(echo "$full_data" | jq '.comments | length')
        if [[ "$comm_len" -gt 0 ]]; then
            echo "## Comentarios (${comm_len})"
            echo ""
            echo "$full_data" | jq -r '.comments[] | "**\(.author)** (\(.created[:10])):\n\(.body)\n"' | head -100
            echo ""
        fi

        echo "---"
        echo "*Documento gerado em $(date '+%Y-%m-%d %H:%M:%S') via API Jira.*"
    } > "$summary_file"
    log_ok "Resumo salvo em $summary_file"

    echo "$ticket_id"
    return 0
}

# ============================================================
# Execucao direta
# ============================================================
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 1 ]]; then
        echo "Uso: $0 TICKET_ID [OUTPUT_DIR]"
        echo ""
        echo "Variaveis de ambiente:"
        echo "  JIRA_BASE       - URL base do Jira (ex: https://meujira.atlassian.net)"
        echo "  JIRA_USER       - Email ou usuario Jira"
        echo "  JIRA_TOKEN      - Token de API do Jira"
        echo ""
        echo "Exemplos:"
        echo "  JIRA_BASE=https://meujira.atlassian.net $0 PROJ-123"
        echo "  $0 PROJ-123 ./tickets/PROJ-123"
        exit 1
    fi
    jira_deep_fetch "$@"
fi
