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

LOG_PREFIX="REFINE"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/utils.sh"

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

    # Limpar temporarios do scan
    rm -f "$py_scan_json" "$py_desc"

    # ============================================================
    # Montar documento via template
    # ============================================================

    local reveal_root
    reveal_root="$(cd "$ticket_dir/../.." && pwd)"
    local script_dir="$reveal_root/lib"
    local template_file="${3:-$reveal_root/templates/refinamento-tecnico-template-improved.md}"

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
    local tasks_list=""
    if [[ -f "$tasks_file" ]]; then
        tasks_list=$(python3 -c "
import json
with open('$tasks_file') as f:
    data = json.load(f)
for t in data.get('tarefas', []):
    jira_key = t.get('jiraKey', '')
    desc = t['descricao'][:80]
    nivel = t.get('nivel', '')
    jira_part = f' ({jira_key})' if jira_key else ''
    print(f\"- **{t['id']}**{jira_part} — {desc} ({nivel}, {t['tipo']})\")
" 2>/dev/null || echo "*Nenhuma subtarefa definida.*")
    else
        tasks_list="*Nenhuma subtarefa definida.*"
    fi

    # ============================================================
    # NOVA SECAO: Observacoes Tecnicas por Task
    # ============================================================
    local technical_observations=""
    if [[ -f "$tasks_file" ]]; then
        technical_observations=$(python3 -c "
import json
with open('$tasks_file') as f:
    data = json.load(f)
tasks = data.get('tarefas', [])
if not tasks:
    print('*Nenhuma subtarefa definida.*')
else:
    print('| Task | Descricao | Observacoes Tecnicas |')
    print('|------|-----------|----------------------|')
    for t in tasks:
        tid = t.get('id', '')
        desc = t.get('descricao', '')[:70]
        obs = t.get('observacoes', '')
        if obs:
            obs_short = obs[:200].replace('|', '\\|').replace('\n', ' ')
        else:
            obs_short = 'Nenhuma observacao tecnica especifica'
        print(f'| {tid} | {desc[:50]} | {obs_short} |')
" 2>/dev/null || echo "*Nenhuma observacao tecnica disponivel*")
    else
        technical_observations="*Nenhum arquivo de tasks encontrado.*"
    fi

    # ============================================================
    # NOVA SECAO: Matriz de Rastreabilidade Negocio-Tecnico
    # ============================================================
    local traceability_matrix=""
    if [[ -f "$questions_file" && -f "$tasks_file" ]]; then
        # Salvar impact em arquivo temp para seguranca
        local py_impact_file="/tmp/_refine_impact_$$.json"
        echo "$impact" > "$py_impact_file"

        traceability_matrix=$(python3 -c "
import json, re, os

STOPWORDS = {'e','de','da','do','das','dos','em','um','uma','para','por','que','se',
             'como','mais','mas','tambem','ja','nao','sim','ou','com','sem','sao',
             'esta','este','estes','estas','isso','aquele','aquela','quem','qual',
             'quais','quando','onde','como','porque','pois','pode','podem','deve',
             'devem','tem','temos','tema','seja','faz','fazer','feito'}

def extract_keywords(text):
    words = re.findall(r'\\b[\\w]+\\b', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]

def load_questions(filepath):
    questions = []
    with open(filepath) as f:
        lines = f.readlines()
    started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|---'):
            started = True
            continue
        if not started:
            continue
        if not stripped or stripped.startswith('|--'):
            continue
        parts = [p.strip() for p in stripped.split('|') if p.strip()]
        if len(parts) >= 2:
            questions.append({
                'id': parts[0],
                'text': parts[1] if len(parts) > 1 else '',
                'categoria': parts[2] if len(parts) > 2 else '',
            })
    return questions

def load_impact(filepath):
    try:
        with open(filepath) as f:
            data = json.load(f)
        return data.get('decisoesTecnicas', [])
    except:
        return []

def load_tasks(filepath):
    with open(filepath) as f:
        data = json.load(f)
    return data.get('tarefas', [])

questions = load_questions('$questions_file')
decisions = load_impact('$py_impact_file')
tasks = load_tasks('$tasks_file')

rows = []
for q in questions:
    q_keywords = extract_keywords(q['text'])
    if not q_keywords:
        continue

    # Find related decisions
    related_decisions = []
    for d in decisions:
        d_text = d.get('decisao', '') + ' ' + d.get('area', '')
        d_keywords = extract_keywords(d_text)
        if any(kw in d_keywords for kw in q_keywords) or any(kw in q_keywords for kw in d_keywords):
            related_decisions.append(d.get('decisao', ''))

    # Find related tasks
    related_tasks = []
    for t in tasks:
        t_text = t.get('descricao', '') + ' ' + t.get('observacoes', '') + ' ' + t.get('tipo', '')
        t_keywords = extract_keywords(t_text)
        if any(kw in t_keywords for kw in q_keywords) or any(kw in q_keywords for kw in t_keywords):
            related_tasks.append(f\"{t.get('id', '')}: {t.get('descricao', '')[:40]}\")

    if related_decisions or related_tasks:
        dec_str = '<br>'.join(related_decisions[:3]) if related_decisions else '-'
        task_str = '<br>'.join(related_tasks[:3]) if related_tasks else '-'
        q_text_esc = q['text'][:60].replace('|', '\\|')
        rows.append(f\"| {q['id']} | {q_text_esc} | {dec_str} | {task_str} |\")

if rows:
    print('| # | Pergunta | Decisao Tecnica Relacionada | Tasks Relacionadas |')
    print('|---|----------|----------------------------|--------------------|')
    for r in rows:
        print(r)
else:
    print('*Nenhum mapeamento automatico encontrado.*')
    print('')
    print('**Instrucao para o Tech Lead:** ')
    print('Preencha manualmente a matriz acima, relacionando cada pergunta de negocio')
    print('as decisoes tecnicas e tasks que ela impacta.')
" 2>/dev/null || echo "*Nao foi possivel gerar a matriz de rastreabilidade*")
        rm -f "$py_impact_file"
    else
        traceability_matrix="*Nao foi possivel gerar (perguntas ou tasks nao disponiveis)*"
    fi

    # Checklist (padrao, pode ser customizado)
    local checklist=$'- [ ] **Analise:** Entendimento do negocio validado com PO\n- [ ] **Perguntas:** Todas as perguntas respondidas\n- [ ] **Modelos:** DTOs/entidades criados\n- [ ] **Interface:** Interface do servico definida\n- [ ] **Integracao:** Endpoint implementado\n- [ ] **Logica:** Regras de negocio implementadas\n- [ ] **Erros:** Tratamento configurado\n- [ ] **Testes unitarios:** Cobertura minima\n- [ ] **Testes integracao:** Fluxo completo\n- [ ] **Configuracao:** Parametros configurados\n- [ ] **Documentacao:** Atualizada\n- [ ] **Review:** Code review realizado\n- [ ] **QA:** Testes de aceite executados'

    # --- NOVAS SECOES: Squad / System / Objetivo / Contexto ---
    local squad=""
    squad=$(jq_get '.customFields.Squad // .customFields.squad // ""')
    if [[ -z "$squad" || "$squad" == "null" ]]; then
        squad="—"
    fi

    local system_name
    system_name=$(python3 -c "
import json
try:
    with open('$scan_file') as f:
        data = json.load(f)
    data = data if isinstance(data, list) else [data]
    names = [p.get('name','') for p in data if p.get('name')]
    print(names[0] if names else '—')
except:
    print('—')
" 2>/dev/null || echo "—")

    # Objetivo funcional — extrai dos campos customizados ou descricao
    local objetivo_funcional=""
    objetivo_funcional=$(jq_get '.customFields.Objetivo // .customFields.objetivo // ""')
    if [[ -z "$objetivo_funcional" || "$objetivo_funcional" == "null" ]]; then
        objetivo_funcional="${clean_desc:-*Descrever o objetivo funcional da demanda*}"
    fi

    # Contexto de negocio — extrai do description.md ou summary
    local py_ticket_text="/tmp/_refine_tickettext_$$.txt"
    echo "$summary $description" > "$py_ticket_text"
    local py_context_out="/tmp/_refine_context_$$.txt"

    python3 -c "
import re, html, os, sys

with open('$py_ticket_text') as f:
    raw = f.read()

# Limpar HTML e normalizar texto
text = re.sub(r'<[^>]+>', ' ', raw)
text = html.unescape(text)
text = re.sub(r'\\\\n|\\n|&#10;', chr(10), text)
text = re.sub(r'&nbsp;', ' ', text)
text = re.sub(r'[ \t]+', ' ', text)
text = re.sub(r'\n\s+', chr(10), text)

sec_keywords = {
    'problema': ['problema', 'atualmente', 'hoje', 'cenário atual', 'situação atual'],
    'impacto': ['impacto', 'afeta', 'consequência', 'consequencia'],
    'objetivo': ['objetivo', 'esperado', 'proposta', 'finalidade', 'propósito', 'proposito'],
    'fluxoatual': ['fluxo atual', 'como funciona', 'processo atual', 'funcionamento atual'],
    'fluxonovo': ['fluxo novo', 'novo fluxo', 'proposto', 'nova funcionalidade', 'novo processo'],
}
defaults = {
    'problema': '*A ser detalhado pelo PO durante o refinamento*',
    'impacto': '*A ser detalhado pelo PO*',
    'objetivo': '*A ser detalhado pelo PO*',
    'fluxoatual': '*Fluxo atual a ser documentado*',
    'fluxonovo': '*Fluxo novo a ser documentado*',
}
current = None
results = {k: [] for k in defaults}
for line in text.split(chr(10)):
    ll = line.lower().strip()
    matched = False
    for sec, kws in sec_keywords.items():
        if any(kw in ll for kw in kws):
            current = sec
            matched = True
            break
    if matched:
        continue
    if re.search(r'^#{1,3}\s|^---|^\*\*|^\- \[', ll):
        current = None
        continue
    if current and line.strip():
        results[current].append(line.strip())

# Escrever cada valor em uma linha separada (sem separador)
with open('$py_context_out', 'w') as fout:
    for k in defaults:
        val = ' '.join(results[k][:3]).strip()
        fout.write((val if val else defaults[k]) + chr(10))
" 2>/dev/null

    # Ler valores do arquivo, linha por linha
    contexto_problema=$(sed -n '1p' "$py_context_out" 2>/dev/null || echo "*A ser detalhado*")
    contexto_impacto=$(sed -n '2p' "$py_context_out" 2>/dev/null || echo "*A ser detalhado*")
    contexto_objetivo=$(sed -n '3p' "$py_context_out" 2>/dev/null || echo "*A ser detalhado*")
    fluxo_atual=$(sed -n '4p' "$py_context_out" 2>/dev/null || echo "*A ser documentado*")
    fluxo_novo=$(sed -n '5p' "$py_context_out" 2>/dev/null || echo "*A ser documentado*")

    rm -f "$py_context_out"

    # === CLASSIFICAR COMPONENTES DO SCAN ===
    local modulos_afetados=""
    local componentes_backend=""
    local componentes_frontend=""
    local componentes_banco=""
    local config_ambiente=""
    local dependencias_externas=""
    local seguranca_permissoes=""

    if [[ -f "$scan_file" ]]; then
        local py_classify="/tmp/_refine_classify_$$.py"
        python3 -c "
import json, re, sys

with open('$scan_file') as f:
    data = json.load(f)
data = data if isinstance(data, list) else [data]

with open('$py_ticket_text') as f:
    ticket_text = f.read().lower()

all_files = []
modulos = []
for proj in data:
    modulos.append(proj.get('name', '?'))
    all_files.extend(proj.get('files', []))

# --- MODULOS AFETADOS ---
print('---MODULOS---')
if modulos:
    for m in modulos:
        print(f'- {m}')
else:
    print('*Nenhum modulo identificado*')

# --- CLASSIFICAR COMPONENTES BACKEND ---
print('---BACKEND---')
controllers = []
services = []
repositories = []
entities = []
dtos = []
outros = []

for f in all_files:
    path = f.get('path', '')
    ftype = f.get('type', '')
    name = path.split('/')[-1] if '/' in path else path
    # Score por relevancia com o ticket
    relevance = sum(1 for kw in ticket_text.split() if len(kw) > 3 and kw.lower() in path.lower())

    if ftype == 'controller' or 'Controller' in name:
        controllers.append((relevance, path))
    elif ftype == 'service' or ('Service' in name and 'Controller' not in name):
        services.append((relevance, path))
    elif ftype == 'repository' or 'Repository' in name:
        repositories.append((relevance, path))
    elif 'domain/' in path or name.startswith('domain.') or ftype == 'entity':
        entities.append((relevance, path))
    elif 'model/' in path or 'DTO' in name or 'Input' in name or 'Output' in name or 'Filter' in name:
        dtos.append((relevance, path))
    elif path.endswith('.java') and relevance > 0:
        outros.append((relevance, path))

def print_group(title, items, max_n=5):
    items.sort(key=lambda x: -x[0])
    relevant = [p for s,p in items if s > 0]
    if not relevant:
        relevant = [p for s,p in items[:max_n]]
    if relevant:
        for p in relevant[:max_n]:
            print(f'- {p}')
    else:
        print(f'*Nenhum {title.lower()} identificado no scan*')

print_group('Controllers', controllers)
print_group('Services', services)
print_group('Repositories', repositories)
print_group('Entities', entities)
print_group('DTOs', dtos)
if outros:
    print_group('Outros arquivos relevantes', outros)

# --- COMPONENTES FRONTEND ---
print('---FRONTEND---')
frontend_files = [f for f in all_files if any(k in f.get('path','').lower() for k in ['/pages/', '/components/', '/services/', '.tsx', '.jsx', '.vue', '/views/'])]
if frontend_files:
    for f in frontend_files[:8]:
        print(f'- {f.get(\"path\",\"\")}')
else:
    print('*Nenhum componente frontend identificado*')

# --- COMPONENTES BANCO ---
print('---BANCO---')
tables_found = set()
for f in all_files:
    path = f.get('path', '')
    if 'changelog' in path.lower() or path.endswith('.sql') or 'liquibase' in path.lower():
        print(f'- {path}')
table_patterns = re.findall(r'\b[A-Z]{3,}(?:_[A-Z]{3,})+\b', ticket_text.upper())
for t in table_patterns[:10]:
    if t not in tables_found:
        tables_found.add(t)
        print(f'- Tabela: {t}')
if not tables_found and not any('changelog' in f.get('path','').lower() for f in all_files):
    print('*Tabelas a definir durante a modelagem*')

# --- CONFIGURACOES DE AMBIENTE ---
print('---CONFIG---')
configs = []
if 'feature' in ticket_text or 'toggle' in ticket_text or 'flag' in ticket_text:
    configs.append('- Feature flag a ser criada para controle da funcionalidade')
if 'application.yml' in ticket_text or 'property' in ticket_text or 'config' in ticket_text:
    configs.append('- Propriedades em application.yml / application-{env}.yml')
if 'timeout' in ticket_text:
    configs.append('- Timeout a ser configurado')
if 'retry' in ticket_text:
    configs.append('- Configuracao de retry')
if 'casa.*decimal' in ticket_text or 'arredondamento' in ticket_text:
    configs.append('- Parametro de arredondamento (casas decimais, criterio) em application.yml')
if not configs:
    configs.append('*Configuracoes a serem definidas durante a implementacao*')
print(chr(10).join(configs))

# --- DEPENDENCIAS EXTERNAS ---
print('---DEPENDENCIAS---')
deps = []
if 'api' in ticket_text or 'integracao' in ticket_text or 'feign' in ticket_text or 'rest' in ticket_text:
    deps.append('- API externa (contrato a ser definido/a confirmar)')
if 'mapstruct' in ticket_text:
    deps.append('- MapStruct (ja existe no projeto)')
if 'lombok' in ticket_text:
    deps.append('- Lombok (ja existe no projeto)')
if 'banco' in ticket_text or 'postgres' in ticket_text or 'postgresql' in ticket_text:
    deps.append('- PostgreSQL (ja configurado no projeto)')
if not deps:
    deps.append('*Dependencias a serem mapeadas durante a implementacao*')
print(chr(10).join(deps))

# --- SEGURANCA E PERMISSOES ---
print('---SEGURANCA---')
seg = []
if 'role' in ticket_text or 'permissao' in ticket_text or 'acesso' in ticket_text or 'autoriza' in ticket_text:
    seg.append('- Roles e permissoes a serem definidas')
if 'admin' in ticket_text:
    seg.append('- Acesso administrativo requerido')
if 'dado.*pessoal' in ticket_text or 'lgpd' in ticket_text:
    seg.append('- Dados pessoais: verificar necessidade de criptografia')
seg.append('*Permissoes a serem mapeadas durante a implementacao (consultar squad de seguranca)*')
print(chr(10).join(seg))
" > "$py_classify" 2>/dev/null

        # Ler resultados
        local current_section=""
        while IFS= read -r line; do
            case "$line" in
                "---MODULOS---") current_section="modulos" ;;
                "---BACKEND---") current_section="backend" ;;
                "---FRONTEND---") current_section="frontend" ;;
                "---BANCO---") current_section="banco" ;;
                "---CONFIG---") current_section="config" ;;
                "---DEPENDENCIAS---") current_section="dependencias" ;;
                "---SEGURANCA---") current_section="seguranca" ;;
                *)
                    if [[ "$current_section" == "modulos" ]]; then
                        modulos_afetados+="$line"$'\n'
                    elif [[ "$current_section" == "backend" ]]; then
                        componentes_backend+="$line"$'\n'
                    elif [[ "$current_section" == "frontend" ]]; then
                        componentes_frontend+="$line"$'\n'
                    elif [[ "$current_section" == "banco" ]]; then
                        componentes_banco+="$line"$'\n'
                    elif [[ "$current_section" == "config" ]]; then
                        config_ambiente+="$line"$'\n'
                    elif [[ "$current_section" == "dependencias" ]]; then
                        dependencias_externas+="$line"$'\n'
                    elif [[ "$current_section" == "seguranca" ]]; then
                        seguranca_permissoes+="$line"$'\n'
                    fi
                    ;;
            esac
        done < "$py_classify"
        rm -f "$py_classify"
    fi

    # Defaults para valores vazios
    modulos_afetados="${modulos_afetados:-*Nenhum modulo identificado*}"
    componentes_backend="${componentes_backend:-*Nenhum componente backend identificado*}"
    componentes_frontend="${componentes_frontend:-}"
    componentes_banco="${componentes_banco:-*Tabelas a definir durante a modelagem*}"
    config_ambiente="${config_ambiente:-*Configuracoes a serem definidas durante a implementacao*}"
    dependencias_externas="${dependencias_externas:-*Dependencias a serem mapeadas durante a implementacao*}"
    seguranca_permissoes="${seguranca_permissoes:-*Permissoes a serem mapeadas durante a implementacao*}"

    # Scan HTML (ja existe — mantido)
    local scan_html_content="${scan_html:-*Nenhum projeto escaneado.*}"

    rm -f "$py_ticket_text"

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
        SQUAD="$squad" \
        SYSTEM="$system_name" \
        SCAN_HTML="$scan_html_content" \
        CHANGE_TYPE="$change_type" \
        DESCRIPTION="$clean_desc" \
        OBJETIVO_FUNCIONAL="$objetivo_funcional" \
        CONTEXTO_PROBLEMA="$contexto_problema" \
        CONTEXTO_IMPACTO="$contexto_impacto" \
        CONTEXTO_OBJETIVO="$contexto_objetivo" \
        FLUXO_ATUAL="$fluxo_atual" \
        FLUXO_NOVO="$fluxo_novo" \
        MODULOS_AFETADOS="$modulos_afetados" \
        COMPONENTES_BACKEND="$componentes_backend" \
        COMPONENTES_FRONTEND="$componentes_frontend" \
        COMPONENTES_BANCO="$componentes_banco" \
        FLOW_DIAGRAM="$flow_diagram" \
        SUGGESTED_FILES="$suggested_files" \
        DECISIONS_TABLE="$decisions_table" \
        RISKS_TABLE="$risks_table" \
        QUESTIONS_TABLE="$questions_table" \
        CONFIG_AMBIENTE="$config_ambiente" \
        DEPENDENCIAS_EXTERNAS="$dependencias_externas" \
        SEGURANCA_PERMISSOES="$seguranca_permissoes" \
        TASKS_LIST="$tasks_list" \
        TECHNICAL_OBSERVATIONS="$technical_observations" \
        TRACEABILITY_MATRIX="$traceability_matrix" \
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
