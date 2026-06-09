#!/usr/bin/env python3
"""Gera texto Jira por subtarefa para a secao 10 do refinamento-tecnico.md.

Uso: python3 generate_per_task_jira_text.py TASKS_JSON IMPACT_JSON

Le: TASKS_JSON (status-tasks.json), IMPACT_JSON (impact-report.json)
Gera: stdout com o texto formatado para copiar para o Jira.
"""

import json
import sys


def decisoes_table(decisoes):
    if not decisoes:
        return '| Decisao | Impacto | Area |\n|---------|---------|------|\n| (Nenhuma decisao pendente) | — | — |'
    lines = ['| Decisao | Impacto | Area |', '|---------|---------|------|']
    for d in decisoes:
        lines.append(f"| {d.get('decisao', '?')} | {d.get('impacto', '—')} | {d.get('area', '—')} |")
    return '\n'.join(lines)


def riscos_table(riscos):
    if not riscos:
        return '| Risco | Probabilidade | Impacto | Mitigacao |\n|-------|-------------|---------|-----------|\n| (Nenhum risco identificado) | — | — | — |'
    lines = ['| Risco | Probabilidade | Impacto | Mitigacao |', '|-------|-------------|---------|-----------|']
    for r in riscos:
        lines.append(f"| {r.get('risco', '?')} | {r.get('probabilidade', '—')} | {r.get('impacto', '—')} | {r.get('mitigacao', '—')} |")
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 3:
        print("Uso: generate_per_task_jira_text.py TASKS_JSON IMPACT_JSON", file=sys.stderr)
        sys.exit(1)

    tasks_path = sys.argv[1]
    impact_path = sys.argv[2]

    with open(tasks_path) as f:
        tasks_data = json.load(f)

    impact = {}
    try:
        with open(impact_path) as f:
            impact = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    tarefas = tasks_data.get('tarefas', [])
    decisoes = impact.get('decisoesTecnicas', [])
    riscos = impact.get('riscosTecnicos', [])

    output_parts = []

    for t in tarefas:
        tid = t['id']
        desc = t['descricao']
        tipo = t['tipo']
        nivel = t['nivel']
        deps = ', '.join(t.get('dependeDe', [])) or '(nenhuma)'
        status = t['status']

        output_parts.append(f"\n---\n\n### TASK {tid} — {desc}\n")

        output_parts.append('| Atributo | Valor |\n')
        output_parts.append('|----------|-------|\n')
        output_parts.append(f"| Nivel | {nivel} |\n")
        output_parts.append(f"| Tipo | {tipo} |\n")
        output_parts.append(f"| Depende de | {deps} |\n")
        output_parts.append(f"| Status | {status} |\n")

        if tipo == 'implementar':
            output_parts.append("\n**O que fazer:**\n")
            steps = [
                'Criar migration Liquibase com a tabela e sequence',
                'Criar entidade JPA com relacionamentos',
                'Criar DTOs de input/output com validacoes',
                'Criar repository com consultas paginadas',
                'Criar mapper (MapStruct) com resolvers',
                'Criar service com Actions (CRUD + validacoes)',
                'Criar controller REST com endpoints',
                'Implementar validacoes de negocio',
            ]
            for i, s in enumerate(steps, 1):
                output_parts.append(f"{i}. {s}\n")

            if 'parametro' in desc.lower() or 'cota' in desc.lower():
                output_parts.append("\n**Campos e Regras:**\n")
                output_parts.append('| Campo | Regra |\n')
                output_parts.append('|-------|-------|\n')
                output_parts.append('| Balancete | Obrigatorio, autocomplete, deve estar ativo |\n')
                output_parts.append('| Perfil | Opcional. Se vazio → vale para todos os perfis |\n')
                output_parts.append('| Qtd casas decimais | Obrigatorio, inteiro, maximo 16 |\n')
                output_parts.append('| Criterio aproximacao | Obrigatorio. ARREDONDADO(1) ou TRUNCADO(2) |\n')

                output_parts.append("\n**Regras de bloqueio:**\n")
                output_parts.append('| Regra | Descricao |\n')
                output_parts.append('|-------|-----------|\n')
                output_parts.append('| Edicao/exclusao bloqueada | Processamento vinculado com status diferente de INICIAL |\n')
                output_parts.append('| Operacoes liberadas | Processamento cancelado |\n')

            output_parts.append("\n**Endpoints:**\n")
            output_parts.append('| Metodo | Rota | Descricao |\n')
            output_parts.append('|--------|------|-----------|\n')

            if 'parametro' in desc.lower() or 'cota' in desc.lower():
                output_parts.append('| GET | /parametros-cota | Listar paginado |\n')
                output_parts.append('| POST | /parametros-cota | Criar |\n')
                output_parts.append('| PUT | /parametros-cota/{id} | Alterar |\n')
                output_parts.append('| DELETE | /parametros-cota/{id} | Excluir |\n')
                output_parts.append('| GET | /parametros-cota/{id} | Buscar por ID |\n')

            output_parts.append("\n**Artefatos:**\n")
            output_parts.append('| Tipo | Descricao |\n')
            output_parts.append('|------|-----------|\n')
            output_parts.append('| Migration Liquibase | Criacao da tabela PARAMETRO_COTA e sequence |\n')
            output_parts.append('| Entidade JPA | Mapeamento ORM com relacionamentos |\n')
            output_parts.append('| DTOs (Input/Output) | Validacoes com @NotBlank, @NotNull, @Max(16) |\n')
            output_parts.append('| Repository | Consultas paginadas e busca por balancete+perfil |\n')
            output_parts.append('| Mapper (MapStruct) | Conversao entidade ↔ DTO com resolvers |\n')
            output_parts.append('| Service + Actions | CRUD com validacoes de negocio |\n')
            output_parts.append('| Controller | Endpoints REST |\n')
            output_parts.append('| Testes | Unitarios e integracao |\n')

        elif tipo == 'alterar-classe':
            output_parts.append("\n**O que fazer:**\n")
            output_parts.append('1. Criar novo validador na cadeia de processamento (@Order(0))\n')
            output_parts.append('2. Alterar a logica de calculo para usar o parametro vigente\n')
            output_parts.append('3. Implementar fallback: parametro especifico → global\n')
            output_parts.append('4. Mapear criterio de aproximacao para RoundingMode\n')
            output_parts.append('5. Executar testes de regressao comparando resultados\n')

            output_parts.append("\n**Arquivos afetados:**\n")
            output_parts.append('| Arquivo | Acao |\n')
            output_parts.append('|---------|------|\n')
            output_parts.append('| CalculoCotaExecutor.java | Alterar |\n')
            output_parts.append('| ProcessamentoCalculoCotaParametroValidator.java | Criar |\n')
            output_parts.append('| CriterioAproximacaoMapper.java | Criar |\n')
            output_parts.append('| ParametroCotaGetAction.java | Adicionar findVigente |\n')

        elif tipo == 'demo':
            output_parts.append("\n**O que fazer:**\n")
            output_parts.append('1. Criar roteiro de demonstracao com 10 cenarios\n')
            output_parts.append('2. Criar collection Postman (CRUD + validacoes + processamento)\n')
            output_parts.append('3. Criar environment Postman com variaveis\n')
            output_parts.append('4. Criar queries SQL para antes/depois\n')

            output_parts.append("\n**Artefatos gerados:**\n")
            output_parts.append('| Artefato | Descricao |\n')
            output_parts.append('|----------|-----------|\n')
            output_parts.append('| roteiro-demo.md | Roteiro de apresentacao com 10 cenarios |\n')
            output_parts.append('| postman-collection.json | Collection com requests organizados por cenario |\n')
            output_parts.append('| postman-environment.json | Environment com variaveis de ambiente |\n')
            output_parts.append('| queries.sql | Queries SQL para demonstrar dados antes/depois |\n')

        output_parts.append(f"\n**Decisoes Tecnicas:**\n{decisoes_table(decisoes)}\n")
        output_parts.append(f"\n**Riscos:**\n{riscos_table(riscos)}\n")

    print(''.join(output_parts), end='')


if __name__ == '__main__':
    main()
