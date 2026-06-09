#!/bin/bash
# ============================================================
# code-review.sh
# Helper para code review em Bitbucket Cloud.
# Usa as mesmas credenciais do Jira (JIRA_USER + JIRA_TOKEN)
# para autenticar na API do Bitbucket.
#
# Uso:
#   code-review.sh <projeto> <PR> info    - Dados do PR
#   code-review.sh <projeto> <PR> diff    - Diff completo
#   code-review.sh <projeto> <PR> files   - Arquivos alterados
#   code-review.sh <projeto> <PR> post <json> - Posta comentários
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="REVIEW"
source "$SCRIPT_DIR/utils.sh"

REVEAL_DIR="$SCRIPT_DIR/.."

# ============================================================
# Carregar credenciais
# Tenta varias fontes na ordem:
#   1. BITBUCKET_APP_PASSWORD (env var, especifica do Bitbucket)
#   2. ~/.bitbucket-credentials (arquivo separado)
#   3. JIRA_TOKEN (fallback — pode funcionar com token multi-produto)
# ============================================================

load_credentials() {
    local user="" token=""

    # 1. BITBUCKET_APP_PASSWORD + JIRA_USER
    if [[ -n "${JIRA_USER:-}" && -n "${BITBUCKET_APP_PASSWORD:-}" ]]; then
        user="$JIRA_USER"
        token="$BITBUCKET_APP_PASSWORD"
        export JIRA_USER="$user"
        export JIRA_TOKEN="$token"
        return 0
    fi

    # 2. ~/.bitbucket-credentials
    if [[ -f "$HOME/.bitbucket-credentials" ]]; then
        IFS=':' read -r user token < "$HOME/.bitbucket-credentials"
        export JIRA_USER="$user"
        export JIRA_TOKEN="$token"
        return 0
    fi

    # 3. ~/.jira-credentials (fallback)
    if [[ -f "$HOME/.jira-credentials" ]]; then
        IFS=':' read -r user token < "$HOME/.jira-credentials"
        export JIRA_USER="$user"
        export JIRA_TOKEN="$token"
        log_info "Usando credenciais do Jira (podem nao funcionar no Bitbucket)"
        return 0
    fi

    # 4. JIRA_USER + JIRA_TOKEN env vars (fallback)
    if [[ -n "${JIRA_USER:-}" && -n "${JIRA_TOKEN:-}" ]]; then
        return 0
    fi

    log_error "Credenciais nao encontradas."
    echo ""
    echo "  Para autenticar no Bitbucket, configure:"
    echo "    export JIRA_USER=\"seu-email\""
    echo "    export BITBUCKET_APP_PASSWORD=\"seu-app-password\""
    echo ""
    echo "  Ou crie ~/.bitbucket-credentials:"
    echo "    email:app_password"
    echo ""
    echo "  App Password: bitbucket.org > Personal settings > App passwords"
    echo "  Permissao necessaria: Pull requests (Read + Write)"
    return 1
}

# ============================================================
# Detectar workspace/repo do projeto alvo
# ============================================================

detect_repo() {
    local project_name="$1"
    local config_file="$REVEAL_DIR/refine-config.local.json"

    if [[ ! -f "$config_file" ]]; then
        config_file="$REVEAL_DIR/refine-config.json"
    fi

    local project_path
    project_path=$(python3 -c "
import json, sys
with open('$config_file') as f:
    data = json.load(f)
for p in data.get('projects', []):
    if p['name'] == '$project_name':
        print(p['path'])
        sys.exit(0)
print('', end='')
" 2>/dev/null || echo "")

    if [[ -z "$project_path" ]]; then
        log_error "Projeto '$project_name' nao encontrado na configuracao"
        return 1
    fi

    local abs_path
    if [[ "$project_path" == /* ]]; then
        abs_path="$project_path"
    else
        abs_path="$(cd "$REVEAL_DIR/$project_path" && pwd)"
    fi

    if [[ ! -d "$abs_path" ]]; then
        log_error "Diretorio do projeto nao encontrado: $abs_path"
        return 1
    fi

    local remote_url
    remote_url=$(cd "$abs_path" && git remote get-url origin 2>/dev/null || echo "")

    if [[ -z "$remote_url" ]]; then
        log_error "Nao foi possivel detectar o remote origin do projeto"
        return 1
    fi

    # Extrair workspace e repo de URLs do Bitbucket Cloud
    # Formato: git@bitbucket.org:workspace/repo.git
    #         https://bitbucket.org/workspace/repo.git
    local workspace repo_slug

    if [[ "$remote_url" =~ bitbucket\.org[:/]([^/]+)/(.+)\.git$ ]]; then
        workspace="${BASH_REMATCH[1]}"
        repo_slug="${BASH_REMATCH[2]}"
    elif [[ "$remote_url" =~ bitbucket\.org[:/]([^/]+)/([^/]+)$ ]]; then
        workspace="${BASH_REMATCH[1]}"
        repo_slug="${BASH_REMATCH[2]}"
    else
        log_error "Remote nao parece ser Bitbucket Cloud: $remote_url"
        return 1
    fi

    echo "$workspace|$repo_slug|$abs_path"
}

# ============================================================
# Requisicao a API do Bitbucket
# ============================================================

bb_api_get() {
    local path="$1"
    local url="https://api.bitbucket.org/2.0${path}"
    local response_file
    response_file=$(mktemp)
    local http_code
    http_code=$(curl -sL -w "%{http_code}" -o "$response_file" \
        -u "$JIRA_USER:$JIRA_TOKEN" \
        -H "Accept: application/json" \
        --connect-timeout 10 --max-time 60 \
        "$url" || echo "000")
    if [[ "$http_code" != "200" && "$http_code" != "201" ]]; then
        log_warn "HTTP $http_code em $path"
        cat "$response_file" >&2
        rm -f "$response_file"
        return 1
    fi
    cat "$response_file"
    rm -f "$response_file"
}

# ============================================================
# Postar comentario inline no PR
# ============================================================

bb_post_comment() {
    local repo_path="$1"
    local pr_id="$2"
    local payload_file="$3"
    local workspace
    workspace=$(echo "$repo_path" | cut -d'|' -f1)
    local repo_slug
    repo_slug=$(echo "$repo_path" | cut -d'|' -f2)

    if [[ ! -f "$payload_file" ]]; then
        log_error "Arquivo de payload nao encontrado: $payload_file"
        return 1
    fi

    # Humanizar conteudo se solicitado
    local working_file="$payload_file"
    if [[ "$HUMANIZE" == true ]]; then
        local humanized_file
        humanized_file=$(mktemp)
        python3 -c "
import json, sys
from pathlib import Path
sys.path.insert(0, '${SCRIPT_DIR}')
from humanize_text import humanize

with open('$payload_file') as f:
    data = json.load(f)

items = data if isinstance(data, list) else [data]
for item in items:
    raw = item.get('content', {}).get('raw', '')
    if raw:
        item['content']['raw'] = humanize(raw, mode='pr')

with open('$humanized_file', 'w') as f:
    json.dump(data if isinstance(data, list) else items[0], f, indent=2)
" 2>/dev/null || cp "$payload_file" "$humanized_file"
        working_file="$humanized_file"
    fi

    local url="https://api.bitbucket.org/2.0/repositories/$workspace/$repo_slug/pullrequests/$pr_id/comments"

    # Posta cada comentario do JSON array individualmente
    local count
    count=$(python3 -c "
import json
with open('$working_file') as f:
    data = json.load(f)
print(len(data) if isinstance(data, list) else 1)
" 2>/dev/null || echo "0")

    if [[ "$count" -eq 0 ]]; then
        log_warn "Nenhum comentario no payload"
        return 0
    fi

    log_info "Postando $count comentario(s) no PR #$pr_id..."

    local i=0
    while [[ $i -lt "$count" ]]; do
        local tmp
        tmp=$(mktemp)
        python3 -c "
import json
with open('$working_file') as f:
    data = json.load(f)
item = data[$i] if isinstance(data, list) else data
print(json.dumps(item))
" > "$tmp" 2>/dev/null

        local http_code
        http_code=$(curl -s -w "%{http_code}" -o /dev/null \
            -u "$JIRA_USER:$JIRA_TOKEN" \
            -H "Content-Type: application/json" \
            --connect-timeout 10 --max-time 30 \
            -X POST -d @"$tmp" \
            "$url" || echo "000")

        if [[ "$http_code" == "201" || "$http_code" == "200" ]]; then
            log_ok "Comentario $((i+1))/$count postado"
        else
            log_warn "Comentario $((i+1))/$count falhou (HTTP $http_code)"
        fi

        rm -f "$tmp"
        i=$((i + 1))
    done

    # Cleanup temp file
    if [[ "$HUMANIZE" == true && -n "${humanized_file:-}" ]]; then
        rm -f "$humanized_file"
    fi

    log_ok "Comentarios postados no PR #$pr_id"
}

# ============================================================
# Main
# ============================================================

if [[ $# -lt 3 ]]; then
    echo "Uso: $0 <projeto> <PR> <acao> [args...] [--no-humanize]"
    echo ""
    echo "  <projeto>       Nome do projeto (ex: dataa-tesouraria)"
    echo "  <PR>            Numero do Pull Request"
    echo ""
    echo "Flags:"
    echo "  --humanize      Humaniza texto dos comentarios (padrao)"
    echo "  --no-humanize   Mantem markdown original"
    echo ""
    echo "Acoes:"
    echo "  info            Dados basicos do PR (JSON)"
    echo "  diff            Diff completo do PR (texto)"
    echo "  files           Lista de arquivos alterados"
    echo "  diffscan <regex> Escaneia o diff por padrao e retorna arquivos+linhas (JSON)"
    echo "  post <json>     Posta comentarios no PR"
    echo ""
    echo "Exemplos:"
    echo "  $0 dataa-tesouraria 123 info"
    echo "  $0 dataa-tesouraria 123 diff"
    echo "  $0 dataa-tesouraria 123 post /tmp/comments.json --no-humanize"
    echo "  $0 dataa-tesouraria 123 diffscan \"replace\(n\.textoNumeracao\""
    echo ""
    echo "Credenciais (ordem de preferencia):"
    echo "  1. ~/.bitbucket-credentials (formato: usuario:token)"
    echo "  2. ~/.jira-credentials (fallback)"
    echo "  3. Env vars: JIRA_USER + BITBUCKET_APP_PASSWORD / JIRA_TOKEN"
    exit 1
fi

HUMANIZE=true
POSITIONAL_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --humanize) HUMANIZE=true ;;
        --no-humanize) HUMANIZE=false ;;
        --help|-h)
            echo "Uso: $0 <projeto> <PR> <acao> [args...] [--no-humanize]"
            echo ""
            echo "  --humanize      Humaniza texto (padrao)"
            echo "  --no-humanize   Mantem markdown original"
            exit 0
            ;;
        *) POSITIONAL_ARGS+=("$arg") ;;
    esac
done

if [[ ${#POSITIONAL_ARGS[@]} -lt 3 ]]; then
    echo "Uso: $0 <projeto> <PR> <acao> [args...] [--no-humanize]"
    echo "Use --help para mais detalhes"
    exit 1
fi

PROJECT_NAME="${POSITIONAL_ARGS[0]}"
PR_ID="${POSITIONAL_ARGS[1]}"
ACTION="${POSITIONAL_ARGS[2]}"
ACTION_ARG="${POSITIONAL_ARGS[3]:-}"

load_credentials

log_info "Detectando repositorio do projeto '$PROJECT_NAME'..."
REPO_INFO=$(detect_repo "$PROJECT_NAME" 2>/dev/null) || {
    log_error "Falha ao detectar repositorio"
    exit 1
}

WORKSPACE=$(echo "$REPO_INFO" | cut -d'|' -f1)
REPO_SLUG=$(echo "$REPO_INFO" | cut -d'|' -f2)
PROJECT_ABS_PATH=$(echo "$REPO_INFO" | cut -d'|' -f3)

log_info "Repositorio: $WORKSPACE/$REPO_SLUG"

case "$ACTION" in
    info)
        log_info "Buscando dados do PR #$PR_ID..."
        bb_api_get "/repositories/$WORKSPACE/$REPO_SLUG/pullrequests/$PR_ID" || exit 1
        ;;

    diff)
        log_info "Buscando diff do PR #$PR_ID..."
        url="https://api.bitbucket.org/2.0/repositories/$WORKSPACE/$REPO_SLUG/pullrequests/$PR_ID/diff"
        curl -sL -u "$JIRA_USER:$JIRA_TOKEN" \
            -H "Accept: text/plain" \
            --connect-timeout 10 --max-time 60 \
            "$url" || {
            log_error "Falha ao buscar diff"
            exit 1
        }
        ;;

    files)
        log_info "Buscando diffstat do PR #$PR_ID..."
        url="https://api.bitbucket.org/2.0/repositories/$WORKSPACE/$REPO_SLUG/pullrequests/$PR_ID/diffstat"
        curl -sL -u "$JIRA_USER:$JIRA_TOKEN" \
            -H "Accept: application/json" \
            --connect-timeout 10 --max-time 60 \
            "$url" | python3 -c "
import json, sys
data = json.load(sys.stdin)
values = data.get('values', [])
files = [{'path': v.get('new', {}).get('path', v.get('path', '')),
          'type': v.get('status', 'modified')} for v in values]
print(json.dumps(files, indent=2))
" 2>/dev/null || echo "[]"
        ;;

    post)
        if [[ -z "$ACTION_ARG" ]]; then
            log_error "Informe o arquivo JSON com os comentarios"
            exit 1
        fi
        bb_post_comment "$REPO_INFO" "$PR_ID" "$ACTION_ARG"
        ;;

    diffscan)
        if [[ -z "$ACTION_ARG" ]]; then
            log_error "Informe o padrao regex para escanear no diff"
            exit 1
        fi
        log_info "Escaneando diff por padrao: $ACTION_ARG"
        url="https://api.bitbucket.org/2.0/repositories/$WORKSPACE/$REPO_SLUG/pullrequests/$PR_ID/diff"
        curl -sL -u "$JIRA_USER:$JIRA_TOKEN" \
            -H "Accept: text/plain" \
            --connect-timeout 10 --max-time 60 \
            "$url" 2>/dev/null | python3 -c "
import json, re, sys

pattern = sys.argv[1]
try:
    regex = re.compile(pattern)
except re.error as e:
    print(json.dumps({'error': str(e)}))
    sys.exit(1)

diff = sys.stdin.read()
results = {}
current_file = None
new_line_offset = 0
in_hunk = False

for line in diff.split('\n'):
    # Detect file header
    m = re.match(r'^\+\+\+ b/(.+)$', line)
    if m:
        current_file = m.group(1)
        results[current_file] = results.get(current_file, [])
        new_line_offset = 0
        in_hunk = False
        continue

    # Detect hunk header
    m = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
    if m:
        new_line_offset = int(m.group(1)) - 1
        in_hunk = True
        continue

    if not current_file or not in_hunk:
        continue

    # Context line (unchanged)
    if line.startswith(' '):
        new_line_offset += 1
        if regex.search(line[1:]):
            results[current_file].append(new_line_offset)

    # Added line
    elif line.startswith('+'):
        new_line_offset += 1
        if regex.search(line[1:]):
            results[current_file].append(new_line_offset)

    # Removed line - don't advance line counter

output = [{'path': k, 'lines': v} for k, v in sorted(results.items()) if v]
print(json.dumps(output, indent=2))
" "$ACTION_ARG" 2>/dev/null || echo "[]"
        ;;

    *)
        log_error "Acao invalida: $ACTION"
        echo "Use: info, diff, files, diffscan, ou post"
        exit 1
        ;;
esac
