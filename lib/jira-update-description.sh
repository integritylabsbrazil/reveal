#!/bin/bash
# ============================================================
# jira-update-description.sh
# Atualiza a descricao do ticket principal no Jira com a
# especificacao completa + breakdown de tasks.
#
# Nao cria subtasks — tudo vai no description do ticket.
#
# Uso: jira-update-description.sh TICKET_ID [--dry-run] [--update-status]
#
#   TICKET_ID      - Chave do ticket (ex: SPR-3420)
#   --dry-run      - Mostra preview sem enviar ao Jira
#   --update-status - Re-gera descricao com status atualizados
#                     (chamado apos cada task concluida)
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="JIRA-DESC"
source "$SCRIPT_DIR/utils.sh"

DRY_RUN=false
UPDATE_STATUS=false
TICKET_ID=""

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --update-status) UPDATE_STATUS=true ;;
        --help|-h)
            cat <<EOF
Uso: $0 TICKET_ID [--dry-run] [--update-status]

  TICKET_ID       - Chave do ticket (ex: SPR-3420)
  --dry-run       - Mostra preview sem enviar ao Jira
  --update-status - Re-gera descricao com status atualizados

Saida (dry-run): markdown completo via stdout + metricas via stderr
Saida (normal):  confirmação da atualizacao via stderr
EOF
            exit 0
            ;;
        *) TICKET_ID="$arg" ;;
    esac
done

if [[ -z "$TICKET_ID" ]]; then
    echo "Uso: $0 TICKET_ID [--dry-run] [--update-status]"
    exit 1
fi

TICKET_DIR="$SCRIPT_DIR/../tickets/$TICKET_ID"

if [[ ! -d "$TICKET_DIR" ]]; then
    log_error "Diretorio do ticket nao encontrado: $TICKET_DIR"
    exit 1
fi

# ============================================================
# Carregar dados
# ============================================================

JIRA_FILE="$TICKET_DIR/jira-data.json"
DESC_FILE="$TICKET_DIR/description.md"
TASKS_FILE="$TICKET_DIR/status-tasks.json"
REF_FILE="$TICKET_DIR/refinamento-tecnico.md"

# Summary do ticket
TICKET_SUMMARY=""
if [[ -f "$JIRA_FILE" ]]; then
    TICKET_SUMMARY=$(jq -r '.basic.summary // .summary // ""' "$JIRA_FILE" 2>/dev/null || echo "")
fi

# Descricao enriquecida
ENRICHED_DESC=""
if [[ -f "$DESC_FILE" ]]; then
    ENRICHED_DESC=$(cat "$DESC_FILE")
fi

# ============================================================
# Montar markdown da descricao completa
# ============================================================

build_description_md() {
    local md=""

    # Cabecalho
    md+="# $TICKET_ID"
    if [[ -n "$TICKET_SUMMARY" ]]; then
        md+=": $TICKET_SUMMARY"
    fi
    md+="\n\n"

    # Se houver description.md enriquecida, extrair secoes principais
    if [[ -n "$ENRICHED_DESC" ]]; then
        # Extrair secao de Objetivo/Contexto (primeiras linhas ate o primeiro ---)
        local objective
        objective=$(echo "$ENRICHED_DESC" | awk 'BEGIN{found=0} /^## (Objetivo|Contexto|Resumo|Historia)/{found=1} found{print} /^---/{if(found) exit}' 2>/dev/null || echo "")
        if [[ -n "$objective" ]]; then
            md+="$objective\n\n"
        fi

        # Extrair Criterios de Aceitacao
        local ca
        ca=$(echo "$ENRICHED_DESC" | awk 'BEGIN{found=0} /^## Critérios|^## Criterios/{found=1} found{print} /^---/{if(found) exit}' 2>/dev/null || echo "")
        if [[ -n "$ca" ]]; then
            md+="\n$ca\n\n"
        fi
    fi

    # Secao: Tasks (sempre incluida)
    md+="## Tasks\n\n"
    if [[ -f "$TASKS_FILE" ]]; then
        local task_count
        task_count=$(jq '.tarefas | length' "$TASKS_FILE" 2>/dev/null || echo 0)
        if [[ "$task_count" -gt 0 ]]; then
            md+="| ID | Descricao |\n"
            md+="|----|-----------|\n"
            while IFS="|" read -r id desc; do
                md+="| $id | $desc |\n"
            done < <(jq -r '.tarefas[] | "\(.id)|\(.descricao[:80])"' "$TASKS_FILE" 2>/dev/null)
            md+="\n"
        else
            md+="*Nenhuma task definida.*\n\n"
        fi
    else
        md+="*Nenhuma task definida.*\n\n"
    fi

    # Secao: Observacoes Tecnicas por Task
    # Usa Python para extrair porque as observacoes contem pipes e multi-linha
    if [[ -f "$TASKS_FILE" ]]; then
        local obs_section
        obs_section=$(python3 -c "
import json, sys
with open('$TASKS_FILE') as f:
    data = json.load(f)
tasks = [t for t in data.get('tarefas', []) if t.get('observacoes', '').strip()]
if not tasks:
    sys.exit(0)
for t in tasks:
    tid = t['id']
    desc = t['descricao'][:80]
    obs = t['observacoes']
    print(f'---')
    print(f'')
    print(f'## Task {tid}: {desc}')
    print(f'')
    print(obs)
    print(f'')
" 2>/dev/null || echo "")
        if [[ -n "$obs_section" ]]; then
            md+="$obs_section\n\n"
        fi
    fi

    # Secao: API Endpoints (do openapi.yaml)
    if [[ -f "$TICKET_DIR/openapi.yaml" ]]; then
        local api_section
        api_section=$(python3 -c "
import yaml

with open('$TICKET_DIR/openapi.yaml') as f:
    spec = yaml.safe_load(f)

if not spec or not spec.get('paths'):
    sys.exit(0)

paths = spec.get('paths', {})
endpoints = []
for path, methods in paths.items():
    for method, details in methods.items():
        endpoints.append((method.upper(), path, details.get('summary', ''), details.get('description', '')))

if endpoints:
    print('')
    print('## API Endpoints')
    print('')
    print('| Metodo | Path | Descricao |')
    print('|--------|------|-----------|')
    for method, path, summary, desc in endpoints:
        desc_text = desc or summary or ''
        print(f'| {method} | \`{path}\` | {desc_text} |')
    print('')

schemas = spec.get('components', {}).get('schemas', {})
if schemas:
    print('')
    print('## Schemas')
    print('')
    for name, schema in schemas.items():
        props = schema.get('properties', {})
        if props:
            print(f'### {name}')
            print('')
            print('| Campo | Tipo | Obrigatorio | Descricao |')
            print('|-------|------|-------------|-----------|')
            req = set(schema.get('required', []))
            for fname, finfo in props.items():
                ftype = finfo.get('type', 'string')
                fdesc = finfo.get('description', '')
                f_req = 'Sim' if fname in req else 'Nao'
                print(f'| \`{fname}\` | \`{ftype}\` | {f_req} | {fdesc} |')
            print('')
" 2>/dev/null || echo "")
        if [[ -n "$api_section" ]]; then
            md+="$api_section\n"
        fi
    fi

    # Secao: Secoes tecnicas do refinamento-tecnico.md
    if [[ -f "$REF_FILE" ]]; then
        # Decisoes Tecnicas
        local decisions
        decisions=$(awk '/## 6\. Decisoes|## Decisoes/,/^---/' "$REF_FILE" 2>/dev/null | grep -v '^---' | head -20 || echo "")
        if [[ -n "$decisions" ]]; then
            md+="## Decisoes Tecnicas\n\n"
            md+="$decisions\n\n"
        fi

        # Riscos
        local risks
        risks=$(awk '/## 7\. Riscos|## Riscos/,/^---/' "$REF_FILE" 2>/dev/null | grep -v '^---' | head -20 || echo "")
        if [[ -n "$risks" ]]; then
            md+="## Riscos\n\n"
            md+="$risks\n\n"
        fi

        # Configuracoes
        local config
        config=$(awk '/## 9\. Configuracoes|## Configuracoes/,/^---/' "$REF_FILE" 2>/dev/null | grep -v '^---' | head -10 || echo "")
        if [[ -n "$config" ]]; then
            md+="## Configuracoes de Ambiente\n\n"
            md+="$config\n\n"
        fi
    fi

    echo -e "$md"
}

# ============================================================
# Gerar descricao e converter para ADF
# ============================================================

log_section "Gerando descricao para $TICKET_ID"

DESCRIPTION_MD=$(build_description_md)
HUMANIZED_MD=$(echo "$DESCRIPTION_MD" | python3 "$SCRIPT_DIR/humanize_text.py" --jira)
DESCRIPTION_JSON=$(echo "$HUMANIZED_MD" | python3 -c "
import json, sys
md = sys.stdin.read()
payload = json.dumps({'observacoes': md})
print(payload)
" | python3 "$SCRIPT_DIR/build_adf.py" 2>/dev/null || echo "")

if [[ -z "$DESCRIPTION_JSON" || "$DESCRIPTION_JSON" == '{"error"'* ]]; then
    log_warn "Falha ao gerar ADF, usando descricao como texto simples"
    DESCRIPTION_JSON=$(jq -n --arg desc "$DESCRIPTION_MD" '{
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": $desc}]}]
    }')
fi

# ============================================================
# Preview ou envio
# ============================================================

if [[ "$DRY_RUN" == true ]]; then
    echo ""
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  JIRA UPDATE DESCRIPTION — DRY RUN               ║"
    echo "║  Ticket: $TICKET_ID"
    echo "║  Nenhuma requisicao sera enviada ao Jira         ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""
    echo "==================== PREVIEW (MARKDOWN HUMANIZADO) ===================="
    echo ""
    echo "$HUMANIZED_MD"
    echo ""
    echo "============================================================"
    echo ""

    md_len=$(echo "$DESCRIPTION_MD" | wc -c)
    json_len=$(echo "$DESCRIPTION_JSON" | wc -c)
    task_count=$(jq '.tarefas | length' "$TASKS_FILE" 2>/dev/null || echo 0)

    echo "--- METRICAS ---"
    echo "  Markdown: ${md_len} bytes"
    echo "  ADF JSON: ${json_len} bytes"
    echo "  Tasks:     ${task_count}"
    echo ""
    echo "  Endpoint: PUT /rest/api/3/issue/$TICKET_ID"
    echo "  Chamada NAO realizada (dry-run)"
    echo ""

    log_ok "Dry-run concluido. Para enviar ao Jira, execute sem --dry-run."
    exit 0
fi

# ============================================================
# Enviar para o Jira
# ============================================================

log_info "Atualizando descricao do ticket $TICKET_ID no Jira..."

# Carregar credenciais e funcao de API do Jira
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
    local method="$1" path="$2" data="${3:-}"
    local url="${JIRA_BASE}${path}"
    local response_file
    response_file=$(mktemp)
    local data_file
    data_file=$(mktemp)
    local curl_args=(-s -w "%{http_code}" -o "$response_file" \
        -u "$JIRA_USER:$JIRA_TOKEN" \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        --connect-timeout 10 --max-time 30)
    if [[ "$method" == "POST" || "$method" == "PUT" ]]; then
        printf '%s' "$data" > "$data_file"
        curl_args+=(-d "@$data_file")
    fi
    local http_code
    http_code=$(curl -X "$method" "${curl_args[@]}" "$url" || echo "000")
    local response_body
    response_body=$(cat "$response_file" 2>/dev/null || echo "sem resposta")
    rm -f "$response_file" "$data_file"
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

JIRA_BASE="${JIRA_BASE:-}"
if [[ -z "$JIRA_BASE" ]]; then
    JIRA_BASE=$(jq -r '.jira.baseUrl // ""' "$SCRIPT_DIR/../refine-config.local.json" 2>/dev/null || true)
fi
if [[ -z "$JIRA_BASE" ]]; then
    JIRA_BASE=$(jq -r '.jira.baseUrl // ""' "$SCRIPT_DIR/../refine-config.json" 2>/dev/null || true)
fi

load_credentials || exit 1

payload=$(jq -n --argjson desc "$DESCRIPTION_JSON" '{fields: {description: $desc}}')

JIRA_API_VERSION="${JIRA_API_VERSION:-3}"
response=$(jira_api "PUT" "/rest/api/${JIRA_API_VERSION}/issue/$TICKET_ID" "$payload") || {
    log_error "Falha ao atualizar descricao do ticket $TICKET_ID"
    exit 1
}

log_ok "Descricao do ticket $TICKET_ID atualizada com sucesso!"
echo "  Tasks incluídas na descricao: $(jq '.tarefas | length' "$TASKS_FILE" 2>/dev/null || echo "?")"

# ============================================================
# Upload openapi.yaml como attachment (se existir)
# ============================================================
jira_upload_attachment() {
    local issue_key="$1" file_path="$2" file_name="$3"
    local url="${JIRA_BASE}/rest/api/${JIRA_API_VERSION}/issue/${issue_key}/attachments"
    local response_file
    response_file=$(mktemp)
    local http_code
    http_code=$(curl -s -w "%{http_code}" -o "$response_file" \
        -u "$JIRA_USER:$JIRA_TOKEN" \
        -H "X-Atlassian-Token: no-check" \
        -F "file=@${file_path};filename=${file_name}" \
        --connect-timeout 10 --max-time 30 \
        "$url" || echo "000")
    local response_body
    response_body=$(cat "$response_file" 2>/dev/null || echo "sem resposta")
    rm -f "$response_file"
    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        log_ok "${file_name} anexado ao ticket $TICKET_ID"
        return 0
    else
        log_warn "Falha ao anexar ${file_name} (HTTP $http_code)"
        echo "$response_body" >&2
        return 1
    fi
}
if [[ -f "$TICKET_DIR/openapi.yaml" ]]; then
    log_info "Enviando openapi.yaml como attachment do ticket $TICKET_ID..."
    jira_upload_attachment "$TICKET_ID" "$TICKET_DIR/openapi.yaml" "openapi.yaml" || true
fi

# Atualizar timestamp
now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq --arg now "$now" '.ultimaAtualizacao = $now' \
    "$TASKS_FILE" > "${TASKS_FILE}.tmp" && mv "${TASKS_FILE}.tmp" "$TASKS_FILE"

exit 0
