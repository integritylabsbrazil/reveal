#!/bin/bash

# ============================================================
# create-ticket-doc.sh  [DEPRECATED]
#
# ATENÇÃO: Este script está DEPRECADO.
# Substituído por:
#   ./gerar-documentacao.sh TICKET_ID   (pipeline completo)
#   ./refine-ticket.sh TICKET_ID --refine  (etapas individuais)
#
# Motivo: create-ticket-doc.sh é monolítico (685 linhas) e não
# suporta configuração via refine-config.local.json, múltiplos
# projetos, subtarefas com senioridade, download de attachments,
# ou renderização por templates.
#
# Use os novos scripts que são modulares, config-driven e
# suportam qualquer projeto (Java, JS/TS, genérico).
# ============================================================
# Script original: busca dados de tickets do Jira via API REST.
# Uso: ./create-ticket-doc.sh TICKET_ID [opcoes]
#
# Variaveis de ambiente esperadas:
#   ATLASSIAN_USER  - Email do usuario Jira
#   ATLASSIAN_TOKEN - Token de API do Jira
# ============================================================

set -euo pipefail

# ============================================================
# Configuracoes
# ============================================================
JIRA_BASE="${JIRA_BASE:-https://meujira.atlassian.net}"
TICKETS_DIR="./tickets"
PROJETOS_DIR="../projetos"

# ============================================================
# Funcao de ajuda
# ============================================================
usage() {
    cat <<EOF
Uso: $0 TICKET_ID [opcoes]

Busca dados de um ticket no Jira e salva em tickets/TICKET_ID/.

Opcoes:
  --fetch-only        Busca dados do Jira e salva (comportamento padrao)
  --generate-demo     Cria estrutura demo-artifacts/ com templates vazios
  --status            Mostra progresso das tasks do ticket
  --deps              Exibe mapa de dependencias entre tasks
  --validate          Valida a consistencia de todos os documentos do ticket
  --generate-context  Gera/atualiza contexto-implementacao.md a partir do status-tasks.json
  --refine            Executa pipeline completo de refinamento (via refine-ticket.sh)
  --list-projects     Lista os projetos de codigo fonte disponiveis
  --list-tickets      Lista tickets ja documentados
  --help, -h          Exibir esta ajuda

Variaveis de ambiente:
  ATLASSIAN_USER      Email do usuario Jira (obrigatorio para fetch)
  ATLASSIAN_TOKEN     Token de API do Jira (obrigatorio para fetch)

Exemplos:
  $0 PROJ-123 --fetch-only
  $0 PROJ-123 --generate-demo
  $0 --list-projects
  $0 --list-tickets
EOF
    exit 0
}

# ============================================================
# Parse de argumentos
# ============================================================
TICKET_ID=""
MODE=""

if [[ $# -eq 0 ]]; then
    usage
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --fetch-only|-f)
            MODE="fetch"
            shift
            ;;
        --list-projects|-p)
            MODE="list-projects"
            shift
            ;;
        --list-tickets|-t)
            MODE="list-tickets"
            shift
            ;;
        --generate-demo|-g)
            MODE="generate-demo"
            shift
            ;;
        --validate|-v)
            MODE="validate"
            shift
            ;;
        --generate-context|-c)
            MODE="generate-context"
            shift
            ;;
        --status|-s)
            MODE="status"
            shift
            ;;
        --deps|-d)
            MODE="deps"
            shift
            ;;
        --refine|-R)
            MODE="refine"
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            if [[ -z "$TICKET_ID" ]]; then
                TICKET_ID="$1"
                # So define MODE como fetch se nenhum modo foi explicitamente definido
                if [[ -z "$MODE" ]]; then
                    MODE="fetch"
                fi
            else
                echo "Erro: argumento desconhecido: $1"
                usage
            fi
            shift
            ;;
    esac
done

# ============================================================
# Listar projetos de codigo fonte
# ============================================================
if [[ "$MODE" == "list-projects" ]]; then
    echo "Projetos de codigo fonte disponiveis:"
    echo ""
    if [[ -d "$PROJETOS_DIR" ]]; then
        for proj in "$PROJETOS_DIR"/*/; do
            nome=$(basename "$proj")
            tipo=""
            if [[ -f "$proj/build.gradle" || -f "$proj/settings.gradle" ]]; then
                tipo="(Java/Gradle)"
                echo "  $nome/ $tipo"
                continue
            elif [[ -f "$proj/pom.xml" ]]; then
                tipo="(Java/Maven)"
                echo "  $nome/ $tipo"
                continue
            elif [[ -f "$proj/package.json" ]]; then
                tipo="(Node.js)"
                echo "  $nome/ $tipo"
                continue
            fi
            echo "  $nome/"
            for sub in "$proj"*/; do
                if [[ -d "$sub" ]]; then
                    sub_nome=$(basename "$sub")
                    if [[ -f "$sub/build.gradle" ]]; then
                        echo "    └── $sub_nome/ (Java/Gradle)"
                    elif [[ -f "$sub/pom.xml" ]]; then
                        echo "    └── $sub_nome/ (Java/Maven)"
                    elif [[ -f "$sub/package.json" ]]; then
                        echo "    └── $sub_nome/ (Node.js)"
                    else
                        echo "    └── $sub_nome/"
                    fi
                fi
            done
        done
    else
        echo "  (nenhum projeto encontrado em $PROJETOS_DIR)"
    fi
    exit 0
fi

# ============================================================
# Listar tickets documentados
# ============================================================
if [[ "$MODE" == "list-tickets" ]]; then
    echo "Tickets documentados:"
    echo ""
    if [[ -d "$TICKETS_DIR" ]]; then
        for ticket_dir in "$TICKETS_DIR"/[A-Z]*-[0-9]*/; do
            if [[ -d "$ticket_dir" ]]; then
                ticket_id=$(basename "$ticket_dir")
                desc_file="$ticket_dir/description.md"
                json_file="$ticket_dir/jira-data.json"
                if [[ -f "$desc_file" ]]; then
                    summary=$(grep -m1 -E '^\*\*(Titulo|Summary|Título):\*\*' "$desc_file" 2>/dev/null | sed 's/.*\*\*[^:]*:\*\* //' || echo "(sem descricao)")
                    echo "  $ticket_id - $summary"
                elif [[ -f "$json_file" ]]; then
                    summary=$(grep -m1 '"summary"' "$json_file" 2>/dev/null | sed 's/.*: "//;s/".*//' || echo "(dados brutos)")
                    echo "  $ticket_id - $summary"
                else
                    echo "  $ticket_id (vazio)"
                fi
            fi
        done
    else
        echo "  (nenhum ticket encontrado)"
    fi
    exit 0
fi

# ============================================================
# Gerar estrutura demo-artifacts/
# ============================================================
if [[ "$MODE" == "generate-demo" ]]; then
    TICKET_DIR="$TICKETS_DIR/$TICKET_ID"
    if [[ ! -d "$TICKET_DIR" ]]; then
        echo "Erro: Ticket $TICKET_ID nao encontrado. Execute --fetch-only primeiro."
        exit 1
    fi

    DEMO_DIR="$TICKET_DIR/demo-artifacts"
    mkdir -p "$DEMO_DIR"

    echo "=== Gerando estrutura demo-artifacts para $TICKET_ID ==="
    echo ""

    if [[ ! -f "$DEMO_DIR/postman-collection.json" ]]; then
        cat > "$DEMO_DIR/postman-collection.json" << 'COLLECTION_EOF'
{
  "info": {
    "name": "{{TICKET_ID}} - Demo",
    "description": "Collection para demo do ticket {{TICKET_ID}}.\n\nPreencher com os cenarios de apresentacao.",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": []
}
COLLECTION_EOF
        echo "  Criado: $DEMO_DIR/postman-collection.json (template)"
    fi

    if [[ ! -f "$DEMO_DIR/postman-environment.json" ]]; then
        cat > "$DEMO_DIR/postman-environment.json" << 'ENV_EOF'
{
  "name": "{{TICKET_ID}} - Ambiente Demo",
  "values": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8080",
      "type": "default",
      "enabled": true
    }
  ],
  "_postman_variable_scope": "environment"
}
ENV_EOF
        echo "  Criado: $DEMO_DIR/postman-environment.json (template)"
    fi

    if [[ ! -f "$DEMO_DIR/queries.sql" ]]; then
        cat > "$DEMO_DIR/queries.sql" << 'SQL_EOF'
-- ============================================
-- Queries SQL para Demo -- {{TICKET_ID}}
-- ============================================
-- Preencher com consultas para demonstrar
-- dados antes/depois da execucao.
-- Usar :nome para parametros.
-- ============================================
SQL_EOF
        echo "  Criado: $DEMO_DIR/queries.sql (template)"
    fi

    echo ""
    echo "=== Estrutura demo-artifacts gerada em $DEMO_DIR ==="
    echo "Preencha os arquivos com os dados especificos do ticket."
    echo "O agente pode gerar o conteudo completo automaticamente."
    exit 0
fi

# ============================================================
# Mostrar status do ticket
# ============================================================
if [[ "$MODE" == "status" ]]; then
    TICKET_DIR="$TICKETS_DIR/$TICKET_ID"
    if [[ ! -f "$TICKET_DIR/status-tasks.json" ]]; then
        echo "Erro: status-tasks.json nao encontrado para $TICKET_ID"
        exit 1
    fi
    python3 -c "
import json, sys
with open('$TICKET_DIR/status-tasks.json') as f:
    data = json.load(f)
tasks = data['tarefas']
total = len(tasks)
concluidas = [t for t in tasks if t['status'] == 'concluido']
pendentes = [t for t in tasks if t['status'] == 'pendente']
andamento = [t for t in tasks if t['status'] == 'em_andamento']
falhou = [t for t in tasks if t['status'] == 'falhou']

projetos = {}
for t in tasks:
    p = t['projeto']
    if p not in projetos:
        projetos[p] = {'tasks': [], 'concluidas': 0}
    projetos[p]['tasks'].append(t)
    if t['status'] == 'concluido':
        projetos[p]['concluidas'] += 1

print(f\"\033[1m{data['ticketId']}\033[0m — {total} tasks\")
for proj, info in projetos.items():
    print(f\"\n  Projeto: {proj}\")
    for t in info['tasks']:
        status_map = {
            'concluido': '\033[32m\u2714\033[0m',
            'pendente': '\033[90m\u23f3\033[0m',
            'em_andamento': '\033[33m\u25b6\033[0m',
            'falhou': '\033[31m\u2718\033[0m',
        }
        ic = status_map.get(t['status'], '\033[90m?\033[0m')
        print(f\"    {ic} {t['id']} {t['descricao'][:70]}\")
    pct = int(info['concluidas'] / len(info['tasks']) * 100)
    print(f\"    \u2550\u2550\u2550 {info['concluidas']}/{len(info['tasks'])} concluidas ({pct}%)\")
print(f\"\n  Total: {len(concluidas)}/{total} concluidas ({int(len(concluidas)/total*100)}%)\")
print(f\"  Pendentes: {len(pendentes)} | Andamento: {len(andamento)} | Falhou: {len(falhou)}\")
" 2>/dev/null || echo "python3 necessario para esta funcao"
    exit 0
fi

# ============================================================
# Mostrar dependencias do ticket
# ============================================================
if [[ "$MODE" == "deps" ]]; then
    TICKET_DIR="$TICKETS_DIR/$TICKET_ID"
    if [[ ! -f "$TICKET_DIR/status-tasks.json" ]]; then
        echo "Erro: status-tasks.json nao encontrado para $TICKET_ID"
        exit 1
    fi
    python3 -c "
import json
with open('$TICKET_DIR/status-tasks.json') as f:
    data = json.load(f)
tasks = data['tarefas']
projs = data.get('projetosEnvolvidos', [])

print(f\"\033[1m{data['ticketId']}\033[0m: Dependencias entre tasks\")

# Mapa de tarefas
task_map = {t['id']: t for t in tasks}

# Agrupar por projeto (match por nome curto ou completo)
def match_projeto(proj_name, task_proj):
    return proj_name == task_proj or proj_name.endswith('/' + task_proj) or task_proj.endswith('/' + proj_name)
for proj in projs:
    proj_tasks = [t for t in tasks if match_projeto(proj, t['projeto'])]
    if not proj_tasks:
        continue
    print(f\"\n  \033[1m{proj}\033[0m\")
    for t in proj_tasks:
        deps = t.get('dependeDe', [])
        if deps:
            dep_str = ', '.join(deps)
            print(f\"    {t['id']} \u2190 {dep_str}\")
        else:
            print(f\"    {t['id']} (independente)\")

# Caminho critico (maior cadeia)
def longest_path(tasks):
    deps_map = {t['id']: t.get('dependeDe', []) for t in tasks}
    memo = {}
    def depth(tid):
        if tid in memo:
            return memo[tid]
        deps = deps_map.get(tid, [])
        if not deps:
            memo[tid] = 1
        else:
            memo[tid] = 1 + max(depth(d) for d in deps)
        return memo[tid]
    max_depth = 0
    critical = []
    for t in tasks:
        d = depth(t['id'])
        if d > max_depth:
            max_depth = d
    # reconstruir caminho
    for t in tasks:
        if depth(t['id']) == max_depth:
            path = [t['id']]
            while task_map[path[-1]].get('dependeDe', []):
                deps = task_map[path[-1]]['dependeDe']
                candidates = [(d, depth(d)) for d in deps]
                candidates.sort(key=lambda x: -x[1])
                path.append(candidates[0][0])
            critical = list(reversed(path))
            break
    return critical

critical = longest_path(tasks)
print(f\"\n  \033[1mCaminho critico:\033[0m {' \u2192 '.join(critical)} ({len(critical)} tasks)\")
" 2>/dev/null || echo "python3 necessario para esta funcao"
    exit 0
fi

# ============================================================
# Validar ticket
# ============================================================
if [[ "$MODE" == "validate" ]]; then
    VALIDATE_SCRIPT="$(dirname "$0")/validate-ticket.sh"
    if [[ -f "$VALIDATE_SCRIPT" ]]; then
        exec bash "$VALIDATE_SCRIPT" "$TICKET_ID"
    else
        echo "Erro: validate-ticket.sh nao encontrado em $(dirname "$0")"
        exit 1
    fi
fi

# ============================================================
# Gerar contexto
# ============================================================
if [[ "$MODE" == "generate-context" ]]; then
    GENERATE_SCRIPT="$(dirname "$0")/generate-context.sh"
    if [[ -f "$GENERATE_SCRIPT" ]]; then
        exec bash "$GENERATE_SCRIPT" "$TICKET_ID"
    else
        echo "Erro: generate-context.sh nao encontrado em $(dirname "$0")"
        exit 1
    fi
fi

# ============================================================
# Refinamento completo (delega para refine-ticket.sh)
# ============================================================
if [[ "$MODE" == "refine" ]]; then
    REFINE_SCRIPT="$(dirname "$0")/refine-ticket.sh"
    if [[ -f "$REFINE_SCRIPT" ]]; then
        exec bash "$REFINE_SCRIPT" "$TICKET_ID" --refine
    else
        echo "Erro: refine-ticket.sh nao encontrado em $(dirname "$0")"
        echo "Execute ./create-ticket-doc.sh --fetch-only primeiro, depois instale refine-ticket.sh"
        exit 1
    fi
fi

# ============================================================
# Validacao do ticket ID
# ============================================================
if [[ -z "$TICKET_ID" ]]; then
    echo "Erro: TICKET_ID e obrigatorio"
    usage
fi

if ! [[ "$TICKET_ID" =~ ^[A-Z][A-Z0-9]+-[0-9]+$ ]]; then
    echo "Aviso: '$TICKET_ID' nao segue o formato esperado (ex: PROJ-123)"
fi

# ============================================================
# Buscar credenciais (ordem: env vars > ~/.jira-credentials)
# ============================================================
if [[ -z "${ATLASSIAN_USER:-}" && -f "$HOME/.jira-credentials" ]]; then
    IFS=':' read -r ATLASSIAN_USER ATLASSIAN_TOKEN < "$HOME/.jira-credentials"
fi

if [[ -z "${ATLASSIAN_USER:-}" || -z "${ATLASSIAN_TOKEN:-}" ]]; then
    echo "Erro: Credenciais Jira nao encontradas."
    echo ""
    echo "Configure de uma das formas:"
    echo ""
    echo "  1. Variaveis de ambiente (prioridade):"
    echo "     export ATLASSIAN_USER='seu.email@empresa.com'"
    echo "     export ATLASSIAN_TOKEN='seu-token-aqui'"
    echo ""
    echo "  2. Arquivo ~/.jira-credentials (formato: email:token):"
    echo "     echo 'email:token' > ~/.jira-credentials"
    echo "     chmod 600 ~/.jira-credentials"
    exit 1
fi

# ============================================================
# Criar diretorio do ticket
# ============================================================
TICKET_DIR="$TICKETS_DIR/$TICKET_ID"
mkdir -p "$TICKET_DIR"

echo "=== Buscando dados do ticket $TICKET_ID no Jira ==="
echo ""

# ============================================================
# Buscar dados na API Jira
# ============================================================
JIRA_URL="$JIRA_BASE/rest/api/3/issue/$TICKET_ID"
echo "URL: $JIRA_URL"

HTTP_CODE=""
RESPONSE_FILE=$(mktemp)

# Fazer a requisicao e capturar codigo HTTP
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
    -u "$ATLASSIAN_USER:$ATLASSIAN_TOKEN" \
    -H "Accept: application/json" \
    "$JIRA_URL" || echo "000")

if [[ "$HTTP_CODE" != "200" ]]; then
    echo "Erro: Jira retornou HTTP $HTTP_CODE"
    if [[ -s "$RESPONSE_FILE" ]]; then
        echo "Resposta: $(head -c 500 "$RESPONSE_FILE")"
    fi
    rm -f "$RESPONSE_FILE"
    exit 1
fi

echo "OK - Ticket encontrado!"
echo ""

# ============================================================
# Processar resposta com jq (se disponivel)
# ============================================================
SUMMARY=""
DESCRIPTION_TEXT=""
PRIORITY=""
STATUS=""
COMPONENTS_JSON=""
ASSIGNEE=""
REPORTER=""
CREATED=""
UPDATED=""
LABELS_JSON=""
FIX_VERSIONS_JSON=""
ISSUE_TYPE=""

if command -v jq &> /dev/null; then
    SUMMARY=$(jq -r '.fields.summary // ""' "$RESPONSE_FILE")
    PRIORITY=$(jq -r '.fields.priority.name // ""' "$RESPONSE_FILE")
    STATUS=$(jq -r '.fields.status.name // ""' "$RESPONSE_FILE")
    COMPONENTS_JSON=$(jq -c '[.fields.components[]?.name // empty]' "$RESPONSE_FILE" 2>/dev/null)
    ASSIGNEE=$(jq -r '.fields.assignee.displayName // ""' "$RESPONSE_FILE")
    REPORTER=$(jq -r '.fields.reporter.displayName // ""' "$RESPONSE_FILE")
    CREATED=$(jq -r '.fields.created // ""' "$RESPONSE_FILE")
    UPDATED=$(jq -r '.fields.updated // ""' "$RESPONSE_FILE")
    LABELS_JSON=$(jq -c '[.fields.labels[]? // empty]' "$RESPONSE_FILE" 2>/dev/null)
    FIX_VERSIONS_JSON=$(jq -c '[.fields.fixVersions[]?.name // empty]' "$RESPONSE_FILE" 2>/dev/null)
    ISSUE_TYPE=$(jq -r '.fields.issuetype.name // ""' "$RESPONSE_FILE")

    # Extrair descricao (pode ser string plana ou ADF - Atlassian Document Format)
    DESCRIPTION_RAW=$(jq -r '.fields.description // ""' "$RESPONSE_FILE")
    if echo "$DESCRIPTION_RAW" | grep -q '"type":"doc"'; then
        # Descricao em ADF - extrair texto recursivamente
        DESCRIPTION_TEXT=$(jq -r '
            .fields.description
            | . as $doc
            | [.. | objects | select(.type == "text") | .text // empty]
            | join("\n")
        ' "$RESPONSE_FILE" 2>/dev/null)
        if [[ -z "$DESCRIPTION_TEXT" ]]; then
            DESCRIPTION_TEXT="[Descricao em formato ADF - veja o rawResponse no JSON]"
        fi
    else
        DESCRIPTION_TEXT="$DESCRIPTION_RAW"
    fi
else
    echo "Aviso: jq nao encontrado. Instale para melhor processamento:"
    echo "  sudo apt-get install jq  (ou brew install jq)"
    echo ""
    SUMMARY=$(grep -oP '(?<="summary":")[^"]*' "$RESPONSE_FILE" 2>/dev/null | head -1 || echo "")
    DESCRIPTION_TEXT="[Descricao nao processada - veja rawResponse no JSON]"
fi

# ============================================================
# Salvar jira-data.json
# ============================================================
JSON_FILE="$TICKET_DIR/jira-data.json"

if command -v jq &> /dev/null; then
    # Construir JSON estruturado
    jq -n \
        --arg id "$TICKET_ID" \
        --arg summary "$SUMMARY" \
        --arg desc "$DESCRIPTION_TEXT" \
        --arg priority "$PRIORITY" \
        --arg status "$STATUS" \
        --arg components "$COMPONENTS_JSON" \
        --arg assignee "$ASSIGNEE" \
        --arg reporter "$REPORTER" \
        --arg created "$CREATED" \
        --arg updated "$UPDATED" \
        --arg labels "$LABELS_JSON" \
        --arg fixVersions "$FIX_VERSIONS_JSON" \
        --arg issuetype "$ISSUE_TYPE" \
        --arg raw "$(cat "$RESPONSE_FILE")" \
        '{
            ticketId: $id,
            summary: $summary,
            descriptionText: $desc,
            priority: $priority,
            status: $status,
            components: ($components | fromjson),
            assignee: $assignee,
            reporter: $reporter,
            created: $created,
            updated: $updated,
            labels: ($labels | fromjson),
            fixVersions: ($fixVersions | fromjson),
            issuetype: $issuetype,
            acceptanceCriteria: "",
            relatedIssues: [],
            rawResponse: $raw
        }' > "$JSON_FILE"
else
    # Sem jq: salvar resposta bruta e um JSON simples
    cat "$RESPONSE_FILE" > "$TICKET_DIR/jira-response-raw.json"
    cat > "$JSON_FILE" <<EOF
{
  "ticketId": "$TICKET_ID",
  "summary": "$SUMMARY",
  "descriptionText": "$DESCRIPTION_TEXT",
  "note": "Dados parciais - instale jq para extracao completa. Resposta bruta em jira-response-raw.json"
}
EOF
fi

echo "  Dados salvos: $JSON_FILE"

# ============================================================
# Salvar jira-summary.md (resumo legivel)
# ============================================================
SUMMARY_FILE="$TICKET_DIR/jira-summary.md"

cat > "$SUMMARY_FILE" <<EOF
# $TICKET_ID: $SUMMARY

| Campo | Valor |
|-------|-------|
| **Status** | $STATUS |
| **Prioridade** | $PRIORITY |
| **Tipo** | $ISSUE_TYPE |
| **Responsavel** | $ASSIGNEE |
| **Solicitante** | $REPORTER |
| **Criado em** | $CREATED |
| **Atualizado em** | $UPDATED |

## Descricao

$DESCRIPTION_TEXT

$(if [[ -n "$COMPONENTS_JSON" ]] && echo "$COMPONENTS_JSON" | jq -e 'length > 0' > /dev/null 2>&1; then
    echo "## Componentes"
    echo ""
    echo "$COMPONENTS_JSON" | jq -r '.[] | "- \(.)"' 2>/dev/null
    echo ""
  fi)

$(if [[ -n "$LABELS_JSON" ]] && echo "$LABELS_JSON" | jq -e 'length > 0' > /dev/null 2>&1; then
    echo "## Labels"
    echo ""
    echo "$LABELS_JSON" | jq -r '.[] | "- \(.)"' 2>/dev/null
    echo ""
  fi)

## Fix Versions

$(if [[ -n "$FIX_VERSIONS_JSON" ]] && echo "$FIX_VERSIONS_JSON" | jq -e 'length > 0' > /dev/null 2>&1; then
    echo "$FIX_VERSIONS_JSON" | jq -r '.[] | "- \(.)"' 2>/dev/null
  else
    echo "- (nenhuma)"
  fi)

---

*Documento gerado em $(date '+%Y-%m-%d %H:%M:%S') via API Jira.*
EOF

echo "  Resumo salvo: $SUMMARY_FILE"

# ============================================================
# Sugerir proximos passos
# ============================================================
echo ""
echo "=== Dados do ticket $TICKET_ID obtidos com sucesso! ==="
echo ""
echo "Arquivos gerados:"
echo "  $JSON_FILE"
echo "  $SUMMARY_FILE"
echo ""
echo "Proximos passos para o agente:"
echo "  1. Leia $JSON_FILE para obter os dados do ticket"
echo "  2. Analise os projetos em $PROJETOS_DIR/"
echo "  3. Identifique os componentes afetados"
echo "  4. Gere os arquivos de documentacao com IA:"
echo "     - description.md"
echo "     - implementation-plan.md"
echo "     - roteiro-demo.md"
echo "     - demo-artifacts/postman-collection.json"
echo "     - demo-artifacts/postman-environment.json"
echo "     - demo-artifacts/queries.sql"
echo "     - contexto-implementacao.md"
echo ""

# ============================================================
# Limpeza
# ============================================================
rm -f "$RESPONSE_FILE"