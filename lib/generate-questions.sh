#!/bin/bash

# ============================================================
# generate-questions.sh
# Gera perguntas para o negocio baseado em gaps de informacao
# no ticket Jira e na analise de codigo.
#
# Uso: source generate-questions.sh
#       generate_questions TICKET_DIR [TEMPLATE_FILE]
# ============================================================

set -euo pipefail

RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'; BLUE='\033[34m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[QUEST]${NC} $1" >&2; }
log_ok()    { echo -e "${GREEN}[QUEST]${NC} $1" >&2; }
log_warn()  { echo -e "${YELLOW}[QUEST]${NC} $1" >&2; }

# ============================================================
# Detectores de gap
# ============================================================

analyze_description_gaps() {
    local desc="$1"

    local gaps="[]"

    # Palavras/vagoes que indicam falta de especificacao
    local vague_patterns=(
        "conforme" "apropad" "adequad" "devidamente" "corretament"
        "normalment" "usualmente" "tipicamente" "eventualmente"
        "necessário" "necessario" "quando aplicável" "quando aplicavel"
        "se aplica" "se for o caso" "quando couber"
    )

    for pattern in "${vague_patterns[@]}"; do
        if echo "$desc" | grep -qi "$pattern"; then
            local context
            context=$(echo "$desc" | grep -i "$pattern" | head -1 | sed 's/^[[:space:]]*//' | head -c 120)
            local question
            question="O que significa exatamente '$(echo "$pattern" | sed 's/./&/')' no contexto: \"${context}...\"? Especificar comportamento esperado."
            gaps=$(echo "$gaps" | jq -c \
                --arg q "$question" \
                --arg c "Especificacao" \
                --arg i "Alto" \
                '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Pre-refinamento", "origem": "descricao_vaga"}]')
        fi
    done

    # Verificar se ha criterios de aceitacao
    if ! echo "$desc" | grep -qi "critério\|criterio\|acceptance\|deve\|should\|expected"; then
        gaps=$(echo "$gaps" | jq -c \
            --arg q "Nao foram encontrados criterios de aceitacao. Quais sao os cenarios de sucesso e falha?" \
            --arg c "Criterios de Aceitacao" \
            --arg i "Alto" \
            '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Pre-refinamento", "origem": "sem_ca"}]')
    fi

    echo "$gaps"
}

analyze_integration_gaps() {
    local desc="$1"
    local gaps="[]"

    # Mencoes a APIs externas sem detalhes
    if echo "$desc" | grep -qi "api\|endpoint\|serviço\|servicio\|integracao\|integracion\|feign\|rest\|soap\|graphql"; then
        if ! echo "$desc" | grep -qi "timeout\|retry\|circuit\|resilien"; then
            gaps=$(echo "$gaps" | jq -c \
                --arg q "Ha integracao com API externa. Qual o SLA esperado? Timeout, retry e circuit breaker sao necessarios?" \
                --arg c "Integracao" \
                --arg i "Alto" \
                '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Pre-refinamento", "origem": "integracao_sem_resiliencia"}]')
        fi
        if ! echo "$desc" | grep -qi "contrato\|swagger\|openapi\|yaml\|wsdl\|spec"; then
            gaps=$(echo "$gaps" | jq -c \
                --arg q "Onde esta o contrato/ especificacao da API (Swagger, OpenAPI, WSDL)?" \
                --arg c "Integracao" \
                --arg i "Alto" \
                '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Pre-refinamento", "origem": "integracao_sem_contrato"}]')
        fi
    fi

    echo "$gaps"
}

analyze_data_gaps() {
    local jira_data="$1"
    local gaps="[]"

    # Verificar acceptanceCriteria vazio
    local ac
    ac=$(echo "$jira_data" | jq -r '.acceptanceCriteria // ""')
    if [[ -z "$ac" || "$ac" == "null" ]]; then
        gaps=$(echo "$gaps" | jq -c \
            --arg q "Quais sao os criterios de aceitacao detalhados? Por favor, descrever cenarios de sucesso, falha e excecao." \
            --arg c "Criterios de Aceitacao" \
            --arg i "Alto" \
            '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Pre-refinamento", "origem": "ac_vazio"}]')
    fi

    echo "$gaps"
}

analyze_toggle_gaps() {
    local desc="$1"
    local gaps="[]"

    if echo "$desc" | grep -qi "toggle\|flag\|feature.?flag\|habilitar\|desabilitar\|enable\|disable\|liga.*desliga"; then
        if ! echo "$desc" | grep -qi "default\|padrão\|padrao\|false\|true\|on\|off"; then
            gaps=$(echo "$gaps" | jq -c \
                --arg q "O toggle mencionado: qual o valor padrao? Deve ser configurado em runtime (refresh) ou requer restart?" \
                --arg c "Configuracao" \
                --arg i "Medio" \
                '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Durante refinamento", "origem": "toggle_sem_default"}]')
        fi
    fi

    echo "$gaps"
}

analyze_error_gaps() {
    local desc="$1"
    local gaps="[]"

    if echo "$desc" | grep -qi "erro\|error\|exception\|falha\|failure\|timeout\|4xx\|5xx\|500\|400"; then
        if ! echo "$desc" | grep -qi "comportamento\|behavior\|deve.*acontecer\|deve.*fazer\|deve.*ocorrer\|o que acontece"; then
            gaps=$(echo "$gaps" | jq -c \
                --arg q "Em cenarios de erro (timeout, HTTP 4xx, HTTP 5xx), qual o comportamento esperado? Deve retentar? Deve falhar silenciosamente?" \
                --arg c "Tratamento de Erros" \
                --arg i "Alto" \
                '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Pre-refinamento", "origem": "erro_sem_comportamento"}]')
        fi
    else
        # Se nao ha mencão a erro mas ha integracao, perguntar
        if echo "$desc" | grep -qi "api\|endpoint\|serviço\|integracao"; then
            gaps=$(echo "$gaps" | jq -c \
                --arg q "Nao foi mencionado tratamento de erros. Qual o comportamento esperado em caso de falha da integracao?" \
                --arg c "Tratamento de Erros" \
                --arg i "Medio" \
                '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Durante refinamento", "origem": "integracao_sem_erro"}]')
        fi
    fi

    echo "$gaps"
}

analyze_security_gaps() {
    local desc="$1"
    local gaps="[]"

    if echo "$desc" | grep -qi "dado\|data\|informa.*\|pessoal\|cpf\|cnpj\|documento\|email\|telefone\|endereco"; then
        if ! echo "$desc" | grep -qi "cripto\|seguran\|privac\|lgpd\|pii\|sensive"; then
            gaps=$(echo "$gaps" | jq -c \
                --arg q "Dados pessoais (CPF/CNPJ, email, telefone) serao trafegados/armazenados? Ha requisitos de criptografia ou LGPD?" \
                --arg c "Seguranca" \
                --arg i "Medio" \
                '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Durante refinamento", "origem": "dados_sensiveis_sem_seguranca"}]')
        fi
    fi

    echo "$gaps"
}

analyze_scope_gaps() {
    local desc="$1"
    local gaps="[]"

    if echo "$desc" | grep -qi "futur.*hist.*\|proxim.*passo\|proxima.*hist.*\|sprint.*futur"; then
        gaps=$(echo "$gaps" | jq -c \
            --arg q "Ha mencao a trabalho futuro. Esta historia inclui apenas a preparacao ou tambem a ativacao no fluxo?" \
            --arg c "Escopo" \
            --arg i "Alto" \
            '. + [{"pergunta": $q, "categoria": $c, "impacto": $i, "prazo": "Pre-refinamento", "origem": "escopo_futuro_mencionado"}]')
    fi

    echo "$gaps"
}

# ============================================================
# Geracao principal
# ============================================================

generate_questions() {
    local ticket_dir="$1"
    local template_file="${2:-}"

    local ticket_id
    ticket_id=$(basename "$ticket_dir")
    local questions_json="[]"

    log_info "Analisando ticket $ticket_id para gerar perguntas ao negocio"

    # Carregar dados do ticket
    local jira_file="$ticket_dir/jira-data.json"
    local jira_data="{}"
    local description=""
    local summary=""

    if [[ -f "$jira_file" ]]; then
        jira_data=$(cat "$jira_file")
        description=$(echo "$jira_data" | jq -r '.basic.description // .descriptionText // .fields.description // ""')
        summary=$(echo "$jira_data" | jq -r '.basic.summary // .summary // ""')
    fi

    # Carregar description.md se existir (mais rica)
    local desc_file="$ticket_dir/description.md"
    if [[ -f "$desc_file" ]]; then
        desc_content=$(cat "$desc_file")
        description="${description} ${desc_content}"
    fi

    # Helper para garantir JSON valido
    safe_json_merge() {
        local base="$1"
        local addition="$2"
        if [[ -z "$addition" ]]; then
            echo "$base"
            return
        fi
        if echo "$addition" | jq -e '. | type == "array"' > /dev/null 2>&1; then
            echo "$base" | jq -c --argjson g "$addition" '. + $g' 2>/dev/null || echo "$base"
        else
            echo "$base"
        fi
    }

    # Analisar gaps
    log_info "Analisando gaps na descricao..."
    local gaps
    gaps=$(analyze_description_gaps "$description")
    questions_json=$(safe_json_merge "$questions_json" "$gaps")

    gaps=$(analyze_integration_gaps "$description")
    questions_json=$(safe_json_merge "$questions_json" "$gaps")

    gaps=$(analyze_data_gaps "$jira_data")
    questions_json=$(safe_json_merge "$questions_json" "$gaps")

    gaps=$(analyze_toggle_gaps "$description")
    questions_json=$(safe_json_merge "$questions_json" "$gaps")

    gaps=$(analyze_error_gaps "$description")
    questions_json=$(safe_json_merge "$questions_json" "$gaps")

    gaps=$(analyze_security_gaps "$description")
    questions_json=$(safe_json_merge "$questions_json" "$gaps")

    gaps=$(analyze_scope_gaps "$description")
    questions_json=$(safe_json_merge "$questions_json" "$gaps")

    # Gerar perguntas unicas (remover duplicatas)
    local unique_questions
    unique_questions=$(echo "$questions_json" | jq -c '[group_by(.pergunta)[] | first]')

    local total
    total=$(echo "$unique_questions" | jq 'length')
    log_info "$total perguntas geradas"

    # Salvar JSON intermediario
    local questions_file="$ticket_dir/perguntas-negocio.json"
    jq -n \
        --arg ticketId "$ticket_id" \
        --arg summary "$summary" \
        --argjson questions "$unique_questions" \
        '{
            ticketId: $ticketId,
            summary: $summary,
            totalPerguntas: ($questions | length),
            perguntas: $questions,
            generatedAt: (now | strftime("%Y-%m-%dT%H:%M:%S"))
        }' > "$questions_file"
    log_ok "Perguntas salvas em $questions_file"

    # Gerar markdown
    local md_file="$ticket_dir/perguntas-negocio.md"
    {
        echo "# Perguntas para o Negocio — $ticket_id"
        echo ""
        echo "**Resumo:** $summary"
        echo ""
        echo "## Pendências de Especificação"
        echo ""
        echo "As perguntas abaixo foram geradas automaticamente com base em gaps"
        echo "identificados na descricao do ticket e na analise de codigo."
        echo ""
        echo "> **Instrucao:** Preencher a coluna **Resposta** e alterar **Status** para Respondida."
        echo ""
        echo "| # | Pergunta | Categoria | Impacto | Prazo | Status | Resposta |"
        echo "|---|----------|-----------|---------|-------|--------|----------|"

        local idx=0
        echo "$unique_questions" | jq -c '.[]' | while IFS= read -r q; do
            idx=$((idx + 1))
            local pergunta categoria impacto prazo
            pergunta=$(echo "$q" | jq -r '.pergunta')
            categoria=$(echo "$q" | jq -r '.categoria')
            impacto=$(echo "$q" | jq -r '.impacto')
            prazo=$(echo "$q" | jq -r '.prazo')

            local status_icon="🔴"
            local status_text="Aberta"

            # Escapar pipes na pergunta
            pergunta=$(echo "$pergunta" | sed 's/|/\\|/g')

            echo "| $idx | $pergunta | $categoria | $impacto | $prazo | $status_icon $status_text | |"
        done

        echo ""
        echo "---"
        echo "*Perguntas geradas em $(date '+%Y-%m-%d %H:%M:%S')*"
    } > "$md_file"
    log_ok "Perguntas salvas em $md_file"

    echo "$unique_questions"
    return 0
}

# ============================================================
# Execucao direta
# ============================================================
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -lt 1 ]]; then
        echo "Uso: $0 TICKET_DIR [TEMPLATE_FILE]"
        echo ""
        echo "Analisa gaps no ticket e gera perguntas para o negocio."
        echo ""
        echo "Exemplos:"
        echo "  $0 ./tickets/PROJ-123"
        echo "  $0 ./tickets/OUTRO-456"
        exit 1
    fi
    generate_questions "$@"
fi
