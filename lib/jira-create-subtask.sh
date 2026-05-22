#!/bin/bash

# ============================================================
# jira-create-subtask.sh
# Cria ou atualiza uma subtask no Jira via API REST.
#
# Uso:
#   Criar:  jira-create-subtask.sh PARENT_KEY SUMMARY DESCRIPTION_JSON
#   Atualizar: jira-create-subtask.sh --update ISSUE_KEY SUMMARY [DESCRIPTION_JSON]
#
#   PARENT_KEY      - Chave do ticket pai (ex: SPR-3413)
#   SUMMARY         - Titulo da subtask (ex: "[BACKEND] - Implementar CRUD")
#   DESCRIPTION_JSON - Descricao em formato ADF (JSON) — opcional
#   ISSUE_KEY       - Chave da issue para atualizar (ex: SPR-3472)
#
# Retorna: o key da subtask criada (ex: SPR-3414) via stdout
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="JIRA-CREATE"
source "$SCRIPT_DIR/utils.sh"

JIRA_BASE="${JIRA_BASE:-https://seudominio.atlassian.net}"
JIRA_API_VERSION="${JIRA_API_VERSION:-3}"

load_credentials() {
    if [[ -f "$HOME/.jira-credentials" ]]; then
        IFS=':' read -r JIRA_USER JIRA_TOKEN < "$HOME/.jira-credentials"
        return 0
    fi
    if [[ -n "${JIRA_USER:-}" && -n "${JIRA_TOKEN:-}" ]]; then
        return 0
    fi
    log_error "Credenciais Jira nao encontradas."
    echo "  Configure JIRA_USER + JIRA_TOKEN como env vars"
    echo "  Ou crie ~/.jira-credentials (formato: usuario:token)"
    return 1
}

jira_api() {
    local method="$1"
    local path="$2"
    local data="${3:-}"
    local url="${JIRA_BASE}${path}"
    local response_file
    response_file=$(mktemp)
    local curl_args=(-s -w "%{http_code}" -o "$response_file" \
        -u "$JIRA_USER:$JIRA_TOKEN" \
        -H "Accept: application/json" \
        --connect-timeout 10 --max-time 30)

    if [[ "$method" == "POST" || "$method" == "PUT" ]]; then
        curl_args+=(-H "Content-Type: application/json" -d "$data")
    fi

    local http_code
    http_code=$(curl -X "$method" "${curl_args[@]}" "$url" || echo "000")

    local response_body
    response_body=$(cat "$response_file" 2>/dev/null || echo "sem resposta")
    rm -f "$response_file"

    if [[ "$http_code" != "200" && "$http_code" != "201" && "$http_code" != "204" ]]; then
        echo "$response_body" >&2
        return 1
    fi

    if [[ "$http_code" == "204" ]]; then
        return 0
    fi

    echo "$response_body"
    return 0
}

create_subtask() {
    local parent_key="$1"
    local summary="$2"
    local description_json="${3:-null}"

    load_credentials || return 1

    local project_key
    project_key=$(echo "$parent_key" | sed 's/-.*//')

    local payload
    payload=$(jq -n \
        --arg project "$project_key" \
        --arg parent "$parent_key" \
        --arg summary "$summary" \
        --argjson desc "$description_json" \
        '{
            fields: {
                project: {key: $project},
                parent: {key: $parent},
                summary: $summary,
                issuetype: {name: "Sub-task"},
                description: $desc
            }
        }')

    local response
    response=$(jira_api "POST" "/rest/api/${JIRA_API_VERSION}/issue" "$payload") || {
        log_error "Falha ao criar subtask: $summary"
        echo "$response" >&2
        return 1
    }

    local created_key
    created_key=$(echo "$response" | jq -r '.key // empty')
    if [[ -z "$created_key" ]]; then
        log_error "Resposta inesperada da API (sem key)"
        echo "$response" >&2
        return 1
    fi

    echo "$created_key"
    return 0
}

delete_subtask() {
    local issue_key="$1"

    load_credentials || return 1

    local response
    response=$(jira_api "DELETE" "/rest/api/${JIRA_API_VERSION}/issue/$issue_key") || {
        log_error "Falha ao deletar subtask $issue_key (HTTP 403 — sem permissao)"
        return 1
    }

    log_ok "Subtask $issue_key deletada"
    echo "$issue_key"
    return 0
}

update_subtask() {
    local issue_key="$1"
    local summary="$2"
    local description_json="${3:-null}"

    load_credentials || return 1

    local payload
    if [[ "$description_json" == "null" ]]; then
        payload=$(jq -n --arg summary "$summary" '{fields: {summary: $summary}}')
    else
        payload=$(jq -n \
            --arg summary "$summary" \
            --argjson desc "$description_json" \
            '{fields: {summary: $summary, description: $desc}}')
    fi

    jira_api "PUT" "/rest/api/${JIRA_API_VERSION}/issue/$issue_key" "$payload" || {
        log_error "Falha ao atualizar subtask $issue_key"
        return 1
    }

    log_ok "Subtask $issue_key atualizada"
    echo "$issue_key"
    return 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ "$1" == "--update" ]]; then
        shift
        if [[ $# -lt 2 ]]; then
            echo "Uso: $0 --update ISSUE_KEY SUMMARY [DESCRIPTION_JSON]"
            exit 1
        fi
        update_subtask "$@"
    elif [[ "$1" == "--delete" ]]; then
        shift
        if [[ $# -lt 1 ]]; then
            echo "Uso: $0 --delete ISSUE_KEY"
            exit 1
        fi
        delete_subtask "$@"
    else
        if [[ $# -lt 2 ]]; then
            echo "Uso: $0 PARENT_KEY SUMMARY [DESCRIPTION_JSON]"
            echo "  Ou: $0 --update ISSUE_KEY SUMMARY [DESCRIPTION_JSON]"
            echo "  Ou: $0 --delete ISSUE_KEY"
            exit 1
        fi
        create_subtask "$@"
    fi
fi
