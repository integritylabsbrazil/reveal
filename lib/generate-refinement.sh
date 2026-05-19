#!/bin/bash

# ============================================================
# generate-refinement.sh
# Gera o documento de refinamento tecnico completo baseado
# nos dados Jira, scan de codigo e perguntas para o negocio.
#
# Uso: source generate-refinement.sh
#       generate_refinement TICKET_DIR [TEMPLATE_FILE]
# ============================================================

set -euo pipefail

RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; BLUE='\033[34m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[REFINE]${NC} $1" >&2; }
log_ok()    { echo -e "${GREEN}[REFINE]${NC} $1" >&2; }
log_warn()  { echo -e "${YELLOW}[REFINE]${NC} $1" >&2; }

# ============================================================
# Analise de impacto tecnico
# ============================================================

analyze_technical_impact() {
    local ticket_dir="$1"
    local jira_data="$2"

    local components_json
    components_json=$(echo "$jira_data" | jq -c '.basic.components // .components // []')
    local issuetype
    issuetype=$(echo "$jira_data" | jq -r '.basic.issuetype // .issuetype // "Task"')
    local summary
    summary=$(echo "$jira_data" | jq -r '.basic.summary // .summary // ""')
    local description
    description=$(echo "$jira_data" | jq -r '.basic.description // .descriptionText // ""')

    # Detectar tipo de alteracao
    local change_types=()
    echo "$summary $description" | grep -qi "criar.*class\|new.*class\|nov" && change_types+=("criacao")
    echo "$summary $description" | grep -qi "modific.*\|alter.*\|atualiz" && change_types+=("alteracao")
    echo "$summary $description" | grep -qi "bpmn\|delegate\|camunda\|processo" && change_types+=("bpmn")
    echo "$summary $description" | grep -qi "api\|endpoint\|feign\|rest" && change_types+=("api")
    echo "$summary $description" | grep -qi "test" && change_types+=("teste")
    echo "$summary $description" | grep -qi "config\|parametro\|property\|yml\|yaml" && change_types+=("configuracao")

    if [[ ${#change_types[@]} -eq 0 ]]; then
        change_types=("indefinido")
    fi

    local types_str
    types_str=$(printf "%s, " "${change_types[@]}" | sed 's/, $//')

    echo "{"
    echo "  \"tipoAlteracao\": \"$types_str\","
    echo "  \"tipoIssue\": \"$issuetype\","
    echo "  \"componentes\": $components_json"

    # Decisoes tecnicas pendentes
    echo '  ,"decisoesTecnicas": ['

    local first=true
    if echo "$summary $description" | grep -qi "toggle\|flag\|feature.?flag"; then
        $first && first=false || echo ","
        echo "    {\"decisao\": \"O toggle deve ser lido em runtime (RefreshScope) ou na inicializacao?\", \"impacto\": \"alto\", \"area\": \"Configuracao\"}"
    fi
    if echo "$summary $description" | grep -qi "api\|endpoint\|feign\|rest\|soap"; then
        $first && first=false || echo ","
        echo "    {\"decisao\": \"A chamada deve ser sincrona ou assincrona? Deve usar asyncBefore no Camunda?\", \"impacto\": \"alto\", \"area\": \"Arquitetura\"}"
    fi
    if echo "$summary $description" | grep -qi "dado.*pessoal\|cpf\|cnpj\|documento"; then
        $first && first=false || echo ","
        echo "    {\"decisao\": \"Os dados pessoais precisam de criptografia em repouso ou em transito?\", \"impacto\": \"medio\", \"area\": \"Seguranca\"}"
    fi

    echo "  ],"

    # Riscos tecnicos
    echo '  "riscosTecnicos": ['
    first=true
    if echo "$summary $description" | grep -qi "integracao\|api\|feign\|esb"; then
        $first && first=false || echo ","
        echo "    {\"risco\": \"Indisponibilidade do sistema externo pode impactar o fluxo\", \"probabilidade\": \"media\", \"impacto\": \"alto\", \"mitigacao\": \"Implementar retry, circuit breaker e fallback\"}"
    fi
    if echo "$summary $description" | grep -qi "dado.*legado\|migracao\|batch\|massivo"; then
        $first && first=false || echo ","
        echo "    {\"risco\": \"Grande volume de dados pode causar timeout ou estouro de memoria\", \"probabilidade\": \"baixa\", \"impacto\": \"alto\", \"mitigacao\": \"Processamento batch com paginacao e limites\"}"
    fi
    if echo "$summary $description" | grep -qi "toggle\|flag"; then
        echo "    {\"risco\": \"Toggle em estado inconsistente entre ambientes\", \"probabilidade\": \"baixa\", \"impacto\": \"medio\", \"mitigacao\": \"Centralizar configuracao no AWS Parameter Store ou similar\"}"
    fi

    echo '  ]'
    echo "}"
}

# ============================================================
# Geracao do documento
# ============================================================

generate_refinement() {
    local ticket_dir="$1"
    local template_file="${2:-}"

    local ticket_id
    ticket_id=$(basename "$ticket_dir")
    local output_file="$ticket_dir/refinamento-tecnico.md"

    log_info "Gerando refinamento tecnico para $ticket_id"

    # Carregar dados
    local jira_file="$ticket_dir/jira-data.json"
    local scan_file="$ticket_dir/impact-report.json"
    local desc_file="$ticket_dir/description.md"
    local questions_file="$ticket_dir/perguntas-negocio.md"
    local tasks_file="$ticket_dir/status-tasks.json"

    local jira_data="{}"
    [[ -f "$jira_file" ]] && jira_data=$(cat "$jira_file")

    local summary
    summary=$(echo "$jira_data" | jq -r '.basic.summary // .summary // "—"')
    local issuetype
    issuetype=$(echo "$jira_data" | jq -r '.basic.issuetype // .issuetype // "—"')
    local priority
    priority=$(echo "$jira_data" | jq -r '.basic.priority // .priority // "—"')
    local status
    status=$(echo "$jira_data" | jq -r '.basic.status // .status // "—"')
    local assignee
    assignee=$(echo "$jira_data" | jq -r '.basic.assignee // .assignee // "—"')
    local reporter
    reporter=$(echo "$jira_data" | jq -r '.basic.reporter // .reporter // "—"')
    local epic_key
    epic_key=$(echo "$jira_data" | jq -r '.epic.key // ""')
    local epic_summary
    epic_summary=$(echo "$jira_data" | jq -r '.epic.summary // ""')
    local description
    description=$(echo "$jira_data" | jq -r '.basic.description // .descriptionText // ""')
    local labels
    labels=$(echo "$jira_data" | jq -r '.basic.labels // [] | join(", ")')
    local components
    components=$(echo "$jira_data" | jq -r '.basic.components // [] | join(", ")')

    # Atualizar descricao com description.md se existir (mais rica)
    if [[ -f "$desc_file" ]]; then
        description=$(cat "$desc_file")
    fi

    # Carregar scan se existir
    local scan_html=""
    if [[ -f "$scan_file" ]]; then
        scan_html=$(python3 -c "
import json, sys
with open('$scan_file') as f:
    data = json.load(f)
data = data if isinstance(data, list) else [data]
for proj in data:
    print(f'### Projeto: {proj.get(\"name\", \"?\")}')
    print(f'')
    print(f'| Atributo | Valor |')
    print(f'|----------|-------|')
    print(f'| **Linguagem** | {proj.get(\"language\", \"?\")} |')
    print(f'| **Build** | {proj.get(\"buildTool\", \"?\")} |')
    print(f'')
    modules = proj.get('modules', [])
    if modules and len(modules) <= 15:
        print('**Modulos:**')
        for m in modules:
            print(f'- {m.get(\"name\", \"?\")}')
        print(f'')
    files = proj.get('files', [])
    if files and len(files) <= 20:
        print('**Arquivos relevantes:**')
        for f in files:
            print(f'- {f.get(\"type\", \"?\")}: {f.get(\"path\", \"?\")}')
        print(f'')
" 2>/dev/null || echo "*Nenhum scan encontrado*")
    fi

    # Analise tecnica
    local impact
    impact=$(analyze_technical_impact "$ticket_dir" "$jira_data")

    # Perguntas
    local questions_html=""
    if [[ -f "$questions_file" ]]; then
        questions_html=$(grep -E '^\| [0-9]' "$questions_file" 2>/dev/null | head -15 || echo "")
    fi

    # Contar tasks se existir status-tasks.json
    local tasks_info=""
    if [[ -f "$tasks_file" ]]; then
        tasks_info=$(python3 -c "
import json
with open('$tasks_file') as f:
    data = json.load(f)
tasks = data.get('tarefas', [])
total = len(tasks)
concluidas = len([t for t in tasks if t['status'] == 'concluido'])
pendentes = len([t for t in tasks if t['status'] == 'pendente'])
print(f'**Total:** {total} tarefas (**Concluidas:** {concluidas} | **Pendentes:** {pendentes})')
" 2>/dev/null || echo "")
    fi

    # Gerar sugestao de arquivos baseado no tipo
    local suggested_files=""
    local change_type
    change_type=$(echo "$impact" | jq -r '.tipoAlteracao')

    if echo "$change_type" | grep -q "criacao"; then
        suggested_files="${suggested_files}
- (novo) \`src/main/java/.../...Service.java\` — Interface do servico
- (novo) \`src/main/java/.../...ServiceImpl.java\` — Implementacao
- (novo) \`src/main/java/.../...Endpoint.java\` — Endpoint Feign/REST
- (novo) \`src/main/java/.../...Client.java\` — Client de integracao
- (novo) \`src/test/java/.../...ServiceTest.java\` — Testes unitarios"
    fi
    if echo "$change_type" | grep -q "alteracao"; then
        suggested_files="${suggested_files}
- (modificar) Identificar classes existentes que precisam de alteracao
- (modificar) Atualizar interfaces e implementacoes conforme novo comportamento
- (modificar) Atualizar constantes/enums se necessario"
    fi
    if echo "$change_type" | grep -q "bpmn"; then
        suggested_files="${suggested_files}
- (novo) \`src/main/java/.../delegate/...Delegate.java\` — Delegate Camunda
- (modificar) \`src/main/resources/bpmn/...bpmn\` — Atualizar fluxo
- (modificar) \`src/main/java/.../...Scope.java\` — Variaveis de escopo"
    fi
    if echo "$change_type" | grep -q "api"; then
        suggested_files="${suggested_files}
- (novo) endpoint Feign para API externa
- (novo) DTOs de request/response
- (modificar) configuracao de timeouts e resiliencia"
    fi
    if echo "$change_type" | grep -q "configuracao"; then
        suggested_files="${suggested_files}
- (modificar) \`application.yml\` ou \`application-default.yml\` — Novos parametros
- (modificar) AWS Parameter Store ou similar — Parametros de ambiente"
    fi

    # ============================================================
    # Montar documento
    # ============================================================

    {
        echo "# Refinamento Técnico — $ticket_id"
        echo ""
        echo "**$summary**"
        echo ""
        echo "---"
        echo ""
        echo "## 1. Dados do Ticket"
        echo ""
        echo "| Campo | Valor |"
        echo "|-------|-------|"
        echo "| **Ticket** | $ticket_id |"
        echo "| **Tipo** | $issuetype |"
        echo "| **Prioridade** | $priority |"
        echo "| **Status** | $status |"
        echo "| **Responsavel** | $assignee |"
        echo "| **Solicitante** | $reporter |"
        echo "| **Componentes** | ${components:--} |"
        echo "| **Labels** | ${labels:--} |"

        if [[ -n "$epic_key" && "$epic_key" != "null" ]]; then
            echo "| **Epico** | $epic_key: $epic_summary |"
        fi

        echo ""

        # 2. Projetos e modulos
        echo "## 2. Projetos e Modulos Afetados"
        echo ""
        if [[ -n "$scan_html" ]]; then
            echo "$scan_html"
        else
            echo "*Nenhum projeto escaneado. Execute o code scan primeiro:*"
            echo ""
            echo '```bash'
            echo "./refine-ticket.sh $ticket_id --scan-impact"
            echo '```'
            echo ""
        fi

        # 3. Visão geral
        echo "## 3. Visao Geral"
        echo ""
        echo "**Tipo de alteracao:** $change_type"
        echo ""
        echo "### Descricao"
        echo ""
        local clean_desc
        if [[ -f "$desc_file" ]]; then
            # Extrair apenas a descricao, ignorando cabecalhos
            clean_desc=$(grep -v '^#' "$desc_file" 2>/dev/null | grep -v '^\*\*' | grep -v '^|---' | head -30 || true)
        else
            clean_desc=$(echo "$description" | sed 's/<[^>]*>//g' | head -20)
        fi
        echo "${clean_desc:-*Sem descricao disponivel*}"
        echo ""

        # 4. Fluxo de dados
        echo "## 4. Fluxo de Dados (Proposto)"
        echo ""
        echo '```'
        echo "[Entrada/Solicitacao]"
        echo "  │"
        echo "  ├─> [Validar toggle/habilitacao]"
        echo "  │     ├─ Desabilitado → log + skip (fluxo existente)"
        echo "  │     └─ Habilitado → continua"
        echo "  │"
        echo "  ├─> [Montar request com dados do escopo/contexto]"
        echo "  │"
        echo "  ├─> [Chamar API/servico externo]"
        echo "  │     ├─ Sucesso → processar response"
        echo "  │     ├─ Erro (timeout) → retry? log? fallback?"
        echo "  │     ├─ Erro (4xx) → log + continuar? parar?"
        echo "  │     └─ Erro (5xx) → retry? circuit breaker?"
        echo "  │"
        echo "  └─> [Atualizar escopo/variaveis com resultado]"
        echo "       │"
        echo "       └─> [Continuar fluxo principal]"
        echo '```'
        echo ""

        # 5. Arquivos sugeridos
        echo "## 5. Arquivos Sugeridos"
        echo ""
        echo "Com base no tipo de alteracao (${change_type}), os seguintes arquivos"
        echo "provavelmente serao criados ou modificados:"
        echo ""
        echo "$suggested_files"
        echo ""

        # 6. Decisoes tecnicas
        echo "## 6. Decisoes Tecnicas Pendentes"
        echo ""
        echo "| Decisao | Impacto | Area |"
        echo "|---------|---------|------|"

        local decisions
        decisions=$(echo "$impact" | jq -c '.decisoesTecnicas[]' 2>/dev/null || true)
        if [[ -n "$decisions" ]]; then
            echo "$impact" | jq -r '.decisoesTecnicas[] | "| \(.decisao) | \(.impacto) | \(.area) |"'
        else
            echo "| (nenhuma decisao pendente identificada) | — | — |"
        fi
        echo ""

        # 7. Riscos
        echo "## 7. Riscos Tecnicos"
        echo ""
        echo "| Risco | Probabilidade | Impacto | Mitigacao |"
        echo "|-------|-------------|---------|-----------|"

        local risks
        risks=$(echo "$impact" | jq -c '.riscosTecnicos[]' 2>/dev/null || true)
        if [[ -n "$risks" ]]; then
            echo "$impact" | jq -r '.riscosTecnicos[] | "| \(.risco) | \(.probabilidade) | \(.impacto) | \(.mitigacao) |"'
        else
            echo "| (nenhum risco identificado) | — | — | — |"
        fi
        echo ""

        # 8. Perguntas para negocio
        echo "## 8. Perguntas para o Negocio"
        echo ""
        if [[ -f "$questions_file" ]]; then
            echo "| # | Pergunta | Categoria | Impacto | Status |"
            echo "|---|----------|-----------|---------|--------|"
            grep -E '^\| [0-9]' "$questions_file" 2>/dev/null | awk -F'|' 'BEGIN{OFS="|"} {print $1, $2, $3, $4, $6}' || echo "| — | (nenhuma pendente) | — | — | — |"
        else
            echo "*Nenhuma pergunta gerada. Execute o modulo de perguntas primeiro:*"
            echo ""
            echo '```bash'
            echo "./refine-ticket.sh $ticket_id --questions"
            echo '```'
        fi
        echo ""

        # 9. Tasks / subtarefas
        echo "## 9. Subtarefas (Proposta)"
        echo ""
        if [[ -n "$tasks_info" ]]; then
            echo "$tasks_info"
            echo ""
            if [[ -f "$tasks_file" ]]; then
                echo "| # | Projeto | Descricao | Status | Tipo |"
                echo "|---|---------|-----------|--------|------|"
                python3 -c "
import json
with open('$tasks_file') as f:
    data = json.load(f)
for t in data.get('tarefas', []):
    proj_short = t['projeto'].split('/')[-1] if '/' in t['projeto'] else t['projeto']
    print(f\"| {t['id']} | {proj_short} | {t['descricao'][:70]} | {t['status']} | {t['tipo']} |\")
" 2>/dev/null || true
            fi
        else
            echo "*Nenhuma subtarefa definida. O refinamento deve gerar a proposta inicial.*"
            echo ""
            echo "**Sugestao de quebra inicial:**"
            echo ""
            echo "1. Modelos de dominio (DTOs/entidades)"
            echo "2. Interface do servico"
            echo "3. Endpoint/cliente de integracao"
            echo "4. Implementacao do servico"
            echo "5. Delegates / orquestracao (se aplicavel)"
            echo "6. Configuracao (toggles, parametros)"
            echo "7. Testes unitarios"
            echo "8. Testes de integracao"
            echo "9. Documentacao / roteiro de demo"
        fi
        echo ""

        # 10. Checklist
        echo "## 10. Checklist de Implementacao"
        echo ""
        echo "- [ ] **Analise:** Entendimento do negocio validado com PO"
        echo "- [ ] **Perguntas:** Todas as perguntas para o negocio respondidas"
        echo "- [ ] **Design:** Documento de arquitetura revisado (se necessario)"
        echo "- [ ] **Modelos:** DTOs/entidades criados conforme especificacao"
        echo "- [ ] **Interface:** Interface do servico definida"
        echo "- [ ] **Integracao:** Endpoint Feign/cliente implementado"
        echo "- [ ] **Logica:** Regras de negocio implementadas"
        echo "- [ ] **Tratamento de erros:** Timeout, retry, fallback configurados"
        echo "- [ ] **Testes unitarios:** Cobertura minima de 80%"
        echo "- [ ] **Testes integracao:** Fluxo completo testado"
        echo "- [ ] **Configuracao:** Parametros em application.yml + AWS/cloud"
        echo "- [ ] **Documentacao:** implementation-plan.md + roteiro-demo.md atualizados"
        echo "- [ ] **Review:** Code review realizado"
        echo "- [ ] **QA:** Testes de aceite executados pelo QA"
        echo ""

        echo "---"
        echo "*Documento gerado em $(date '+%Y-%m-%d %H:%M:%S') pelo sistema de refinamento tecnico*"
    } > "$output_file"

    log_ok "Refinamento tecnico salvo em $output_file"
    return 0
}

# ============================================================
# Execucao direta
# ============================================================
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 1 ]]; then
        echo "Uso: $0 TICKET_DIR [TEMPLATE_FILE]"
        echo ""
        echo "Gera documento de refinamento tecnico completo."
        echo ""
        echo "Exemplos:"
        echo "  $0 ./tickets/PROJ-123"
        echo "  $0 ./tickets/OUTRO-456"
        exit 1
    fi
    generate_refinement "$@"
fi
