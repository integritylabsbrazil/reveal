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
    local jira_file="$ticket_dir/jira-data.json"
    local desc_file="$ticket_dir/description.md"

    # Helper para ler do JSON com fallback silencioso
    jira_get() { jq -r "$1" "$jira_file" 2>/dev/null || echo ""; }

    local components_json
    components_json=$(jira_get '.basic.components // .components // []')
    local issuetype
    issuetype=$(jira_get '.basic.issuetype // .issuetype // "Task"')
    local summary
    summary=$(jira_get '.basic.summary // .summary // ""')
    local description
    description=$(jira_get '.basic.descriptionRendered // .basic.description // ""')

    # Atualizar descricao com description.md se existir (mais rica)
    if [[ -f "$desc_file" ]]; then
        description=$(cat "$desc_file")
    fi

    # Determinar tipos de alteracao baseado no conteudo
    local change_types=()
    if echo "$summary $description" | grep -qi "parametro\|parametrização\|config\|casa.*decimal\|arredondamento"; then
        change_types+=("configuracao")
        change_types+=("alteracao")
    fi
    if echo "$summary $description" | grep -qi "criar\|novo\|nova\|implementar\|adicionar"; then
        change_types+=("criacao")
    fi
    if echo "$summary $description" | grep -qi "api\|endpoint\|feign\|integracao\|rest"; then
        change_types+=("api")
    fi
    if echo "$summary $description" | grep -qi "bpmn\|camunda\|delegate\|processo\|fluxo"; then
        change_types+=("bpmn")
    fi
    if [[ ${#change_types[@]} -eq 0 ]]; then
        change_types+=("alteracao")
    fi

    local types_str
    types_str=$(printf "%s, " "${change_types[@]}" | sed 's/, $//')

    echo "{"
    echo "  \"tipoAlteracao\": \"$types_str\","
    echo "  \"tipoIssue\": \"$issuetype\","
    echo "  \"componentes\": $components_json"

    # Salvar change_types em arquivo temp para uso posterior
    echo "${change_types[@]}" > "/tmp/_refine_changetypes_$$"

    # Decisoes tecnicas pendentes
    echo '  ,"decisoesTecnicas": ['

    local first=true
    if echo "$summary $description" | grep -qi "toggle\|flag\|feature.?flag\|parametro\|parametrização\|parametriza"; then
        $first && first=false || echo ","
        echo "    {\"decisao\": \"O parametro deve ser lido em runtime (RefreshScope) ou apenas na inicializacao?\", \"impacto\": \"alto\", \"area\": \"Configuracao\"}"
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
    if echo "$summary $description" | grep -qi "toggle\|flag\|parametro\|parametrização\|config"; then
        $first && first=false || echo ","
        echo "    {\"risco\": \"Parametro inconsistente entre ambientes (dev/hml/prd)\", \"probabilidade\": \"baixa\", \"impacto\": \"medio\", \"mitigacao\": \"Centralizar configuracao no AWS Parameter Store ou similar\"}"
    fi
    if echo "$summary $description" | grep -qi "casa.*decimal\|arredondamento"; then
        $first && first=false || echo ","
        echo "    {\"risco\": \"Diferenca de arredondamento entre modulo novo e sistema legado\", \"probabilidade\": \"media\", \"impacto\": \"alto\", \"mitigacao\": \"Testes comparativos com cenarios reais de arredondamento\"}"
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

    # Helper para ler do JSON com fallback silencioso
    [[ -f "$jira_file" ]] || jira_file="/dev/null"
    jq_get() { jq -r "$1" "$jira_file" 2>/dev/null || echo "—"; }

    local summary
    summary=$(jq_get '.basic.summary // .summary // "—"')
    local issuetype
    issuetype=$(jq_get '.basic.issuetype // .issuetype // "—"')
    local priority
    priority=$(jq_get '.basic.priority // .priority // "—"')
    local ticket_status
    ticket_status=$(jq_get '.basic.status // .status // "—"')
    local assignee
    assignee=$(jq_get '.basic.assignee // .assignee // "—"')
    local reporter
    reporter=$(jq_get '.basic.reporter // .reporter // "—"')
    local epic_key
    epic_key=$(jq_get '.epic.key // ""')
    local epic_summary
    epic_summary=$(jq_get '.epic.summary // ""')
    local description
    description=$(jq_get '.basic.descriptionRendered // .basic.description // ""')
    local labels
    labels=$(jq_get '.basic.labels // [] | join(", ")')
    local components
    components=$(jq_get '.basic.components // [] | join(", ")')

    # Atualizar descricao com description.md se existir (mais rica)
    if [[ -f "$desc_file" ]]; then
        description=$(cat "$desc_file")
    fi

    # Carregar scan se existir
    local scan_html=""
    local scan_files_json="[]"
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
    print(f'**Total de arquivos mapeados:** {len(files)}')
    if files:
        print(f'')
        print(f'**Arquivos mais relevantes (controllers/servicos):**')
        count = 0
        for f in files:
            if f.get('type') in ('controller', 'service') and count < 15:
                print(f'- {f.get(\"type\", \"?\")}: {f.get(\"path\", \"?\")}')
                count += 1
        if count == 0:
            for f in files[:15]:
                print(f'- {f.get(\"type\", \"?\")}: {f.get(\"path\", \"?\")}')
        print(f'')
" 2>/dev/null || echo "*Nenhum scan encontrado*")
        scan_files_json=$(python3 -c "
import json
with open('$scan_file') as f:
    data = json.load(f)
data = data if isinstance(data, list) else [data]
all_files = []
for proj in data:
    all_files.extend(proj.get('files', []))
print(json.dumps(all_files))
" 2>/dev/null || echo "[]")
    fi

    # Analise tecnica
    local impact
    impact=$(analyze_technical_impact "$ticket_dir")

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

    # Gerar sugestao de arquivos baseado no scan real + tipo de alteracao
    local suggested_files=""
    local change_type
    change_type=$(echo "$impact" | jq -r '.tipoAlteracao')

    local change_types_file="/tmp/_refine_changetypes_$$"

    # Salvar dados para Python via arquivos temporarios (evita problemas de escaping)
    local py_scan_json="/tmp/_refine_scanjson_$$.json"
    echo "$scan_files_json" > "$py_scan_json"
    local py_desc="/tmp/_refine_desc_$$.txt"
    echo "$summary $description" > "$py_desc"

    suggested_files=$(python3 -c "
import json, sys

with open('$py_scan_json') as f:
    try:
        all_files = json.load(f)
    except:
        all_files = []

with open('$py_desc') as f:
    ticket_text = f.read().lower()

if not all_files:
    print('Nenhum arquivo escaneado no projeto')
    sys.exit(0)

keywords = ['cota', 'balancete', 'parametro', 'decimal', 'arredondamento',
            'patrimonial', 'plano', 'contabil', 'indexador']

scored = []
for f in all_files:
    path_lower = f.get('path', '').lower()
    ftype = f.get('type', '')
    score = 0
    for kw in keywords:
        if kw in path_lower:
            score += 1
    if ftype in ('controller', 'service'):
        score += 2
    scored.append((score, f))

scored.sort(key=lambda x: -x[0])

print('### Arquivos existentes potencialmente afetados')
print('')
relevant = [f for s, f in scored if s > 0][:15]
if relevant:
    for f in relevant:
        ftype = f.get('type', 'arquivo')
        path = f.get('path', '')
        print(f'- ({ftype}) {path}')
else:
    for f in all_files:
        if f.get('type') in ('controller', 'service'):
            path = f.get('path', '')
            print(f'- ({f.get(\"type\")}) {path}')
print('')
print('### Sugestoes de criacao/alteracao')
print('')
change_types_raw = '$change_type'
if 'configuracao' in change_types_raw:
    print('- (criar) DTO para parametrizacao de casas decimais (ex: ParametroCotaDecimalDTO)')
    print('- (criar) Servico de configuracao de parametro (ex: ParametroCotaService)')
    print('- (criar) Controller/Endpoint para CRUD do parametro (ex: ParametroCotaController)')
    print('- (criar) Repository/DAO para persistencia do parametro (ex: ParametroCotaRepository)')
    print('- (modificar) Entidade de plano/balancete para incluir campo de casas decimais')
    print('- (modificar) application.yml — Adicionar configuracao padrao de casas decimais')
if 'alteracao' in change_types_raw and 'configuracao' not in change_types_raw:
    print('- (modificar) Identificar classes existentes que precisam de alteracao')
    print('- (modificar) Atualizar interfaces e implementacoes conforme novo comportamento')
if 'criacao' in change_types_raw:
    print('- (criar) Interface do servico')
    print('- (criar) Implementacao do servico com regras de negocio')
    print('- (criar) Testes unitarios')
if 'api' in change_types_raw:
    print('- (criar) DTOs de request/response')
    print('- (criar) Cliente Feign para API externa')
    print('- (modificar) Configuracao de timeouts e resiliencia')
print('- (criar) Testes unitarios para as novas classes')
print('- (criar) Testes de integracao para o fluxo completo')
" 2>/dev/null || echo "*Nenhuma sugestao gerada*")

    # Limpar temporarios
    rm -f "$py_scan_json" "$py_desc"

    # ============================================================
    # Montar documento via template
    # ============================================================

    local reveal_root
    reveal_root="$(cd "$ticket_dir/../.." && pwd)"
    local script_dir="$reveal_root/lib"
    local template_file="${3:-$reveal_root/templates/refinamento-tecnico-template.md}"

    # --- Preparar secoes dinâmicas ---

    # Epic
    local epic=""
    if [[ -n "$epic_key" && "$epic_key" != "null" ]]; then
        epic="$epic_key: $epic_summary"
    fi

    # Campos personalizados
    local custom_fields
    custom_fields=$(jq_get '.customFields // {} | to_entries[] | "| \(.value.name // .key) | \(.value.value // \"\") |"' | head -30 || true)

    # Descricao limpa
    local clean_desc
    if [[ -f "$desc_file" ]]; then
        clean_desc=$(grep -v '^#' "$desc_file" 2>/dev/null | grep -v '^\*\*' | grep -v '^|---' | head -30 || true)
    elif echo "$description" | grep -q '^{"type":"doc"'; then
        local adf_tmp
        adf_tmp=$(mktemp)
        echo "$description" > "$adf_tmp"
        clean_desc=$(python3 -c "
import json, sys
with open('$adf_tmp') as f:
    data = json.load(f)
texts = []
def extract(node):
    if isinstance(node, dict):
        if node.get('type') == 'text' and node.get('text'):
            texts.append(node['text'])
        for v in node.values():
            extract(v)
    elif isinstance(node, list):
        for item in node:
            extract(item)
extract(data)
print('\n'.join(texts[:30]))
" 2>/dev/null)
        rm -f "$adf_tmp"
    else
        clean_desc=$(echo "$description" | sed 's/<[^>]*>//g' | sed 's/&nbsp;//g; s/&amp;/\&/g; s/&lt;/\</g; s/&gt;/\>/g' | head -20)
    fi
    clean_desc="${clean_desc:-*Sem descricao disponivel*}"

    # Fluxograma (adaptado ao tipo)
    local flow_diagram
    if echo "$change_type" | grep -q "configuracao"; then
        flow_diagram=$'[Menu Principal]\n  │\n  └─> [Funcionalidade]\n        │\n        ├─> [Validar permissao]\n        │     ├─ Negado → erro\n        │     └─ Permitido → continua\n        │\n        ├─> [Executar configuracao]\n        │     ├─ Salvar alteracao\n        │     └─ Log auditoria\n        │\n        └─> [Exibir resultado]'
    else
        flow_diagram=$'[Entrada]\n  │\n  ├─> [Validar toggle]\n  │     ├─ Desabilitado → skip\n  │     └─ Habilitado → continua\n  │\n  ├─> [Montar request]\n  │\n  ├─> [Chamar API/servico]\n  │     ├─ Sucesso → processar\n  │     ├─ Erro timeout → retry?\n  │     ├─ Erro 4xx → log\n  │     └─ Erro 5xx → circuit breaker?\n  │\n  └─> [Atualizar escopo]\n       │\n       └─> [Continuar fluxo]'
    fi

    # Decisoes
    local decisions_table
    decisions=$(echo "$impact" | jq -c '.decisoesTecnicas[]' 2>/dev/null || true)
    if [[ -n "$decisions" ]]; then
        decisions_table=$(echo "$impact" | jq -r '.decisoesTecnicas[] | "| \(.decisao) | \(.impacto) | \(.area) |"' 2>/dev/null)
    else
        decisions_table="| (nenhuma) | — | — |"
    fi

    # Riscos
    local risks_table
    risks=$(echo "$impact" | jq -c '.riscosTecnicos[]' 2>/dev/null || true)
    if [[ -n "$risks" ]]; then
        risks_table=$(echo "$impact" | jq -r '.riscosTecnicos[] | "| \(.risco) | \(.probabilidade) | \(.impacto) | \(.mitigacao) |"' 2>/dev/null)
    else
        risks_table="| (nenhum) | — | — | — |"
    fi

    # Perguntas
    local questions_table=""
    if [[ -f "$questions_file" ]]; then
        questions_table=$'| # | Pergunta | Categoria | Impacto |\n|---|----------|-----------|---------|\n'
        questions_table+=$(grep -E '^\| [0-9]' "$questions_file" 2>/dev/null | awk -F'|' 'BEGIN{OFS="|"} {print $1, $2, $3, $4}' || echo "| — | (nenhuma) | — | — |")
    else
        questions_table="*Nenhuma pergunta gerada. Execute o modulo de perguntas primeiro.*"
    fi

    # Tasks
    local tasks_table=""
    if [[ -f "$tasks_file" ]]; then
        tasks_table=$'| # | Projeto | Descricao | Status | Tipo |\n|---|---------|-----------|--------|------|\n'
        tasks_table+=$(python3 -c "
import json
with open('$tasks_file') as f:
    data = json.load(f)
for t in data.get('tarefas', []):
    proj_short = t['projeto'].split('/')[-1] if '/' in t['projeto'] else t['projeto']
    print(f\"| {t['id']} | {proj_short} | {t['descricao'][:70]} | {t['status']} | {t['tipo']} |\")
" 2>/dev/null || true)
    else
        tasks_table="*Nenhuma subtarefa definida.*"
    fi

    # Checklist (padrao, pode ser customizado)
    local checklist=$'- [ ] **Analise:** Entendimento do negocio validado com PO\n- [ ] **Perguntas:** Todas as perguntas respondidas\n- [ ] **Modelos:** DTOs/entidades criados\n- [ ] **Interface:** Interface do servico definida\n- [ ] **Integracao:** Endpoint implementado\n- [ ] **Logica:** Regras de negocio implementadas\n- [ ] **Erros:** Tratamento configurado\n- [ ] **Testes unitarios:** Cobertura minima\n- [ ] **Testes integracao:** Fluxo completo\n- [ ] **Configuracao:** Parametros configurados\n- [ ] **Documentacao:** Atualizada\n- [ ] **Review:** Code review realizado\n- [ ] **QA:** Testes de aceite executados'

    # Scan HTML
    local scan_html_content="${scan_html:-*Nenhum projeto escaneado.*}"

    # --- Renderizar template ---
    python3 "$script_dir/render_template.py" "$template_file" \
        TICKET_ID="$ticket_id" \
        SUMMARY="$summary" \
        ISSUE_TYPE="$issuetype" \
        PRIORITY="$priority" \
        STATUS="$ticket_status" \
        ASSIGNEE="$assignee" \
        REPORTER="$reporter" \
        COMPONENTS="${components:--}" \
        EPIC="$epic" \
        CUSTOM_FIELDS="$custom_fields" \
        SCAN_HTML="$scan_html_content" \
        CHANGE_TYPE="$change_type" \
        DESCRIPTION="$clean_desc" \
        FLOW_DIAGRAM="$flow_diagram" \
        SUGGESTED_FILES="$suggested_files" \
        DECISIONS_TABLE="$decisions_table" \
        RISKS_TABLE="$risks_table" \
        QUESTIONS_TABLE="$questions_table" \
        TASKS_TABLE="$tasks_table" \
        CHECKLIST="$checklist" \
        DATE="$(date '+%Y-%m-%d %H:%M:%S')" \
        > "$output_file"

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
