#!/bin/bash

# generate-index.sh
# Gera INDEX.md com a lista de todos os tickets documentados e status das tarefas.
# Uso: ./generate-index.sh

set -euo pipefail

TICKETS_DIR="./tickets"

if [[ ! -d "$TICKETS_DIR" ]]; then
    echo "Nenhum ticket encontrado em $TICKETS_DIR"
    exit 0
fi

INDEX_FILE="$TICKETS_DIR/INDEX.md"

{
    echo "# Índice de Tickets"
    echo ""
    echo "Lista de tickets documentados neste repositório."
    echo ""
    echo "| Ticket | Resumo | Tarefas | Progresso |"
    echo "|--------|--------|---------|-----------|"

    for ticket_dir in "$TICKETS_DIR"/[A-Z]*-[0-9]*/; do
        if [[ ! -d "$ticket_dir" ]]; then
            continue
        fi

        ticket_id=$(basename "$ticket_dir")
        desc_file="$ticket_dir/description.md"
        json_file="$ticket_dir/jira-data.json"
        tasks_file="$ticket_dir/status-tasks.json"

        # Extrair resumo
        summary=""
        if [[ -f "$desc_file" ]]; then
            summary=$(grep -m1 -E '^\*\*(Titulo|Summary|Título):\*\*' "$desc_file" 2>/dev/null | sed 's/.*\*\*[^:]*:\*\* //' || true)
            if [[ -z "$summary" ]]; then
                summary=$(head -1 "$desc_file" 2>/dev/null | sed -n 's/^# [A-Z]*-[0-9]*: //p' || true)
            fi
        fi
        if [[ -z "$summary" && -f "$json_file" ]]; then
            if command -v jq &> /dev/null; then
                summary=$(jq -r '.basic.summary // ""' "$json_file")
            else
                summary=$(grep -m1 '"summary"' "$json_file" 2>/dev/null | sed 's/.*: "//;s/".*//' || true)
            fi
        fi
        if [[ -z "$summary" ]]; then
            summary="(sem resumo)"
        fi

        # Contar tarefas (se existir status-tasks.json)
        if [[ -f "$tasks_file" ]]; then
            if command -v jq &> /dev/null; then
                total=$(jq -r '.tarefas | length' "$tasks_file")
                concluidas=$(jq -r '[.tarefas[] | select(.status == "concluido")] | length' "$tasks_file")
                canceladas=$(jq -r '[.tarefas[] | select(.status == "cancelado")] | length' "$tasks_file")
                pendentes=$(jq -r '[.tarefas[] | select(.status == "pendente")] | length' "$tasks_file")
                em_andamento=$(jq -r '[.tarefas[] | select(.status == "em_andamento")] | length' "$tasks_file")
                falhou=$(jq -r '[.tarefas[] | select(.status == "falhou")] | length' "$tasks_file")
            else
                # Fallback com python3 quando jq nao estiver disponivel
                if command -v python3 &> /dev/null; then
                    eval "$(python3 -c "
import json
with open('$tasks_file') as f:
    d = json.load(f)
    tasks = d.get('tarefas', [])
    total = len(tasks)
    concluidas = sum(1 for t in tasks if t.get('status') == 'concluido')
    canceladas = sum(1 for t in tasks if t.get('status') == 'cancelado')
    pendentes = sum(1 for t in tasks if t.get('status') == 'pendente')
    em_andamento = sum(1 for t in tasks if t.get('status') == 'em_andamento')
    falhou = sum(1 for t in tasks if t.get('status') == 'falhou')
    print(f'total={total}; concluidas={concluidas}; canceladas={canceladas}; pendentes={pendentes}; em_andamento={em_andamento}; falhou={falhou}')
")"
                else
                    total=0; concluidas=0; canceladas=0; pendentes=0; em_andamento=0; falhou=0
                fi
            fi
        else
            total=0; concluidas=0; canceladas=0; pendentes=0; em_andamento=0; falhou=0
        fi

        # Montar colunas
        resolvidas=$((concluidas + canceladas))
        if [[ "$total" -gt 0 ]]; then
            tarefas_str="$total tarefas"
            if [[ "$resolvidas" -eq "$total" ]]; then
                progresso="$concluidas/$total"
            elif [[ "$em_andamento" -gt 0 ]]; then
                progresso="$concluidas/$total"
            elif [[ "$falhou" -gt 0 ]]; then
                progresso="$concluidas/$total !"
            else
                progresso="$concluidas/$total"
            fi
        else
            tarefas_str="(n/a)"
            progresso="(sem tasks)"
        fi

        echo "| [$ticket_id](./$ticket_id/) | $summary | $tarefas_str | $progresso |"
    done

    echo ""
    echo "---"
    echo "*Gerado em $(date '+%Y-%m-%d %H:%M:%S')*"
} > "$INDEX_FILE"

echo "Índice atualizado: $INDEX_FILE"
echo "$(grep -c '^| \[' "$INDEX_FILE") tickets listados."