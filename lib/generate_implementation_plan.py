#!/usr/bin/env python3
"""Gera implementation-plan.md rico a partir de jira-data, impact-report, status-tasks.

Uso: python3 generate_implementation_plan.py TICKET_DIR
"""

import json
import os
import re
import sys
from datetime import datetime


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        content = f.read().strip()
        if not content:
            return default
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return default


def get_custom_field(jira_data, name):
    for v in jira_data.get('customFields', {}).values():
        if isinstance(v, dict) and v.get('name') == name:
            return v.get('value', '')
    return ''


def detect_stack(scan_data):
    if not scan_data:
        return {}
    lang = scan_data.get('language', '').lower()
    build = scan_data.get('buildTool', '').lower()
    info = {}

    if lang == 'java':
        info['linguagem'] = 'Java 11'
        info['framework'] = 'Spring Boot 2.7.x'
        if build == 'gradle':
            info['build'] = 'Gradle'
            info['gerenciador'] = 'Gradle (settings.gradle)'
        elif 'maven' in build or build == 'mvn':
            info['build'] = 'Maven 3.8+'
            info['gerenciador'] = 'Maven (pom.xml)'
        else:
            info['build'] = 'Maven/Gradle'
        info['banco'] = 'PostgreSQL'
        info['mapeamento'] = 'MapStruct + Lombok'
        info['testes'] = 'JUnit + Mockito'
    elif lang in ('javascript', 'typescript', 'react', 'node'):
        info['linguagem'] = lang.capitalize()
        info['framework'] = 'React/Node.js'
        info['build'] = 'npm/yarn'
        if lang == 'node':
            info['framework'] = 'Node.js + Express'
        info['testes'] = 'Jest/Vitest'
    else:
        info['linguagem'] = lang.capitalize() if lang else 'Pendente'
        info['framework'] = 'Pendente'
        info['build'] = 'Pendente'

    # Extrair de README/AGENTS se disponível
    docs = scan_data.get('projectDocs', {})
    readme = docs.get('readme', '') or ''
    agents = docs.get('agents', '') or ''
    for text in [readme, agents]:
        for line in text.split('\n'):
            l = line.strip().lower()
            if 'spring boot' in l:
                m = re.search(r'(\d+\.\d+(?:\.\d+)?)', l)
                if m:
                    info['framework'] = f'Spring Boot {m.group(1)}'
            if 'java' in l:
                m = re.search(r'java\s*(\d+(?:\+)?)', l)
                if m:
                    info['linguagem'] = f'Java {m.group(1)}'
            if 'maven' in l and 'build' not in info.get('build', '').lower():
                m = re.search(r'maven\s*([\d.]+)', l)
                if m:
                    info['build'] = f'Maven {m.group(1)}'
                else:
                    info['build'] = 'Maven'
            if 'postgresql' in l or 'postgres' in l:
                info['banco'] = 'PostgreSQL'
            if 'liquibase' in l:
                info['migracoes'] = 'Liquibase'
            if 'mapstruct' in l:
                info['mapeamento'] = 'MapStruct + Lombok'
            if 'lombok' in l:
                if 'mapeamento' not in info:
                    info['mapeamento'] = 'Lombok'

    return info


def detect_base_package(scan_data):
    if not scan_data:
        return 'com.exemplo.projeto'
    packages = scan_data.get('packages', [])
    if not packages:
        return 'com.exemplo.projeto'
    if isinstance(packages, list):
        longest = max(packages, key=len) if packages else 'com.exemplo'
        parts = longest.split('.')
        if len(parts) >= 4:
            return '.'.join(parts[:4])
        return '.'.join(parts[:3]) if len(parts) >= 3 else longest
    if isinstance(packages, dict):
        sorted_pkgs = sorted(packages.items(), key=lambda x: -x[1])
        if sorted_pkgs:
            top = sorted_pkgs[0][0]
            parts = top.split('.')
            if len(parts) >= 4:
                return '.'.join(parts[:4])
            return '.'.join(parts[:3]) if len(parts) >= 3 else top
    return 'com.exemplo.projeto'


def extract_class_examples(scan_data):
    docs = scan_data.get('projectDocs', {}) if scan_data else {}
    examples = {}
    for key, label in [('controllerExamples', 'Controllers'),
                       ('serviceExamples', 'Services'),
                       ('entityExamples', 'Entities')]:
        vals = docs.get(key, [])
        if vals and isinstance(vals, list):
            examples[label] = [v.split('/')[-1] for v in vals[:5]]
    return examples


def extract_package_structure(scan_data, base_pkg):
    if not scan_data:
        return ''
    packages = scan_data.get('packages', [])
    if not isinstance(packages, list):
        return ''
    # Filtrar apenas os que comecam com o pacote base
    relevant = sorted(set(p for p in packages if p.startswith(base_pkg)))
    if not relevant:
        return ''
    # Agrupar segundo nivel
    modules = set()
    for p in relevant:
        parts = p.split('.')
        if len(parts) >= 5:
            modules.add('.'.join(parts[:5]))
        elif len(parts) >= 4:
            modules.add('.'.join(parts[:4]))
    if not modules:
        modules = set(relevant[:5])
    return '\n'.join(sorted(f'- `{m}`' for m in modules)[:10])


def extract_endpoints(tasks, base_pkg, domain_slug):
    endpoints = []
    for t in tasks:
        desc = t.get('descricao', '').lower()
        tipo = t.get('tipo', '')
        if 'crud' in desc or tipo in ('implementar',):
            endpoints.extend([
                ('GET', f'/api/{domain_slug}', 'Listar (com filtros)'),
                ('POST', f'/api/{domain_slug}', 'Incluir'),
                ('PUT', f'/api/{domain_slug}/{{id}}', 'Alterar'),
                ('DELETE', f'/api/{domain_slug}/{{id}}', 'Excluir'),
            ])
        if 'processamento' in desc or 'calculo' in desc:
            endpoints.append(
                ('POST', f'/api/{domain_slug}/processar', 'Executar processamento')
            )
    return endpoints


def extract_entities_from_requirements(jira_data, custom_fields_text):
    # Tenta inferir entidades dos requisitos
    desc = jira_data.get('basic', {}).get('description', '') or ''
    if isinstance(desc, dict):
        desc = str(desc)
    text = (custom_fields_text or '') + ' ' + desc
    entities = set()
    # Palavras que parecem entidades (substantivos compostos com inicial maiúscula,
    # ex: "Balancete", "ParametroCota", "ContaContabil")
    candidates = re.findall(r'\b[A-Z][a-záéíóúâêôãç]{2,}(?:[A-Z][a-záéíóúâêôãç]+)*\b', text)
    # Filtrar palavras obvias que nao sao entidades
    stopwords = {
        'Será', 'Seriam', 'Temos', 'Ser', 'Para', 'Com', 'Sobre', 'Entre',
        'Após', 'Antes', 'Através', 'Desde', 'Durante', 'Mediante',
        'Então', 'Porém', 'Também', 'Todas', 'Todos', 'Ambos', 'Ambas',
        'Aceita', 'Apenas', 'Ainda', 'Assim', 'Através', 'Contudo',
        'Deverá', 'Devem', 'Estão', 'Existem', 'Mais', 'Menos',
        'Mesmo', 'Mesma', 'Muitos', 'Muitas', 'Outros', 'Outras',
        'Parte', 'Pode', 'Podem', 'Poder', 'Pelas', 'Pelos',
        'Porque', 'Possui', 'Possuem', 'Quando', 'Sendo', 'Seria',
        'Sobre', 'Somente', 'Todos', 'Total', 'Através',
        'Através', 'Alguns', 'Algumas', 'Aonde', 'Atrás', 'Cada',
        'Cerca', 'Como', 'Contra', 'Depois', 'Diante', 'Dentro',
        'Dessa', 'Desse', 'Destes', 'Diversos', 'Diversas',
        'Durante', 'Enquanto', 'Entretanto', 'Existe', 'Existir',
        'Maior', 'Maiores', 'Melhor', 'Menor', 'Menores',
        'Nenhum', 'Nenhuma', 'Nessa', 'Nesse', 'Nestes', 'Neste',
        'Nele', 'Nela', 'Neles', 'Nelas', 'Perante',
        'Portanto', 'Própria', 'Próprio', 'Próprios',
        'Qualquer', 'Senão', 'Sob', 'Sobre', 'Sobretudo',
        'Suficiente', 'Tampouco', 'Tendo', 'Tido', 'Tiver',
        'Todavia', 'Tornar', 'Torna', 'Tornam',
    }
    # So aceitar palavras com >5 chars e que parecam substantivos compostos
    # (evitar verbos, artigos, preposicoes)
    verb_like = {        'Alterar', 'Alteração', 'Alterações', 'Criar', 'Incluir',
                 'Excluir', 'Editar', 'Gravar', 'Limpar', 'Pesquisar',
                 'Validar', 'Manter', 'Efetuar', 'Acessar',
                 'Demais', 'Todos', 'Todas', 'Dados', 'Cenários',
                 'Cenário', 'Filtros', 'Campos', 'Campo', 'Valor',
                 'Valores', 'Ações', 'Ação', 'Opção', 'Opções',
                 'Regras', 'Regra', 'Tabela', 'Tipo', 'Tipos',
                 'Ordem', 'Ordem', 'Lista', 'Itens', 'Item',
                 'Nome', 'Código', 'Códigos', 'Status',
                 'Observação', 'Observações', 'Número', 'Números',
                 'Conforme', 'Usando', 'Usar', 'Exemplo', 'Exemplos'}
    for c in candidates:
        if c not in stopwords and c not in verb_like and len(c) > 5:
            entities.add(c)
    return entities


def build_task_table(tasks):
    lines = []
    lines.append('| ID | Descrição | Nível | Tipo | Depende de |')
    lines.append('|----|-----------|-------|------|------------|')
    for t in tasks:
        deps = ', '.join(t.get('dependeDe', [])) or '-'
        lines.append(f"| {t['id']} | {t['descricao'][:60]} | {t.get('nivel', '-')} | {t.get('tipo', '-')} | {deps} |")
    return '\n'.join(lines)


def build_dependency_diagram(tasks):
    lines = []
    for t in tasks:
        deps = t.get('dependeDe', [])
        if deps:
            for d in deps:
                lines.append(f"  {d} ──→ {t['id']}")
    if not lines:
        return '  (nenhuma dependência)'
    return '\n'.join(lines)


def build_risks_table(jira_data, keywords):
    risks = []
    desc = jira_data.get('basic', {}).get('description', '') or ''
    if isinstance(desc, dict):
        desc = str(desc)
    text = (desc or '') + ' ' + get_custom_field(jira_data, 'Requisitos Funcionais')

    if keywords.get('needs_calculation'):
        risks.append(('Diferença de arredondamento entre novo cálculo e legado', 'Média', 'Alto',
                      'Testes comparativos com cenários reais'))
        risks.append(('Quebra em cenários existentes', 'Média', 'Alto',
                      'Atualizar cenários de teste conforme especificação'))

    if keywords.get('needs_validation'):
        risks.append(('Regras de validação inconsistentes', 'Baixa', 'Médio',
                      'Validar com PO e revisar requisitos'))

    if not risks:
        risks.append(('Mudança de escopo durante implementação', 'Baixa', 'Médio',
                       'Alinhamento contínuo com PO'))

    lines = ['| Risco | Probabilidade | Impacto | Mitigação |',
             '|-------|-------------|---------|-----------|']
    for r in risks:
        lines.append(f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} |')
    return '\n'.join(lines)


def build_endpoint_table(endpoints):
    if not endpoints:
        return ''
    lines = ['| Método | Rota | Descrição |',
             '|--------|------|-----------|']
    for m, r, d in endpoints:
        lines.append(f'| {m} | `{r}` | {d} |')
    return '\n'.join(lines)


def build_class_examples_section(examples):
    if not examples:
        return ''
    lines = ['### Exemplos de Classes Existentes no Projeto']
    for label, names in examples.items():
        lines.append(f'\n**{label}:**')
        for n in names:
            lines.append(f'- `{n}`')
    return '\n'.join(lines)


def build_stack_table(info):
    if not info:
        return ''
    lines = ['| Tecnologia |',
             '|-----------|']
    for k, v in info.items():
        label = k.capitalize()
        if k == 'linguagem':
            label = 'Linguagem'
        elif k == 'framework':
            label = 'Framework'
        elif k == 'build':
            label = 'Build'
        elif k == 'banco':
            label = 'Banco'
        elif k == 'mapeamento':
            label = 'Mapeamento'
        elif k == 'testes':
            label = 'Testes'
        elif k == 'migracoes':
            label = 'Migrações'
        lines.append(f'| {label} | {v} |')
    return '\n'.join(lines)


def build_entity_table(entities):
    if not entities:
        return ''
    lines = ['Possíveis entidades/domínios identificados nos requisitos:']
    for e in sorted(entities):
        lines.append(f'- `{e}`')
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Uso: generate_implementation_plan.py TICKET_DIR", file=sys.stderr)
        sys.exit(1)

    ticket_dir = sys.argv[1]

    # Carregar dados
    jira_data = load_json(os.path.join(ticket_dir, 'jira-data.json'))
    scan_data = load_json(os.path.join(ticket_dir, 'impact-report.json'))
    tasks_data = load_json(os.path.join(ticket_dir, 'status-tasks.json'))

    if not jira_data:
        print("[PLAN] ERRO: jira-data.json nao encontrado", file=sys.stderr)
        sys.exit(1)

    if not tasks_data:
        print("[PLAN] ERRO: status-tasks.json nao encontrado", file=sys.stderr)
        sys.exit(1)

    ticket_id = tasks_data.get('ticketId', jira_data.get('ticketId', 'TICKET'))
    summary = jira_data.get('basic', {}).get('summary', '')
    description = jira_data.get('basic', {}).get('description', '') or ''
    if isinstance(description, dict):
        description = str(description)
    tasks = tasks_data.get('tarefas', [])

    # Se scan_data for lista, pegar o primeiro (projeto unico por enquanto)
    if isinstance(scan_data, list):
        scan_data = scan_data[0] if scan_data else None

    # Extrair dados
    info = detect_stack(scan_data)
    base_pkg = detect_base_package(scan_data)
    examples = extract_class_examples(scan_data)
    keywords = {}
    if tasks:
        has_crud = any('crud' in t.get('descricao', '').lower() for t in tasks)
        has_calc = any('processamento' in t.get('descricao', '').lower() or
                       'calculo' in t.get('descricao', '').lower() for t in tasks)
        keywords = {'needs_calculation': has_calc, 'needs_validation': has_crud}

    custom_text = get_custom_field(jira_data, 'Requisitos Funcionais')
    entities = extract_entities_from_requirements(jira_data, custom_text)

    # Determinar nome do dominio para endpoints
    domain_lower = ''
    for t in tasks:
        d = t.get('descricao', '')
        # Extrair o nome do dominio (ex: "de Parametrização Cota Patrimonial")
        m = re.search(r'de\s+(.+?)(?:\s+(?:com|em|no|na|para|e)|\s*$)', d)
        if m:
            domain_lower = m.group(1).strip().lower()
            break
    if not domain_lower:
        domain_lower = 'funcionalidade'
    # Limpar: remover sufixos como "alterar", "criar"
    domain_lower = re.sub(r'\s+(alterar|criar|editar|excluir|listar)\s*$', '', domain_lower).strip()
    # Normalizar slug: transliterar acentos e cedilha
    slug_chars = []
    for c in domain_lower:
        slug_chars.append({
            'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n',
        }.get(c, c))
    safe = ''.join(slug_chars)
    domain_slug = re.sub(r'[^a-z0-9]+', '-', safe).strip('-')

    package_structure = extract_package_structure(scan_data, base_pkg)
    endpoints = extract_endpoints(tasks, base_pkg, domain_slug)

    # --- Gerar o documento ---
    lines = []
    lines.append(f'# Plano de Implementação — {ticket_id}')
    lines.append('')
    if summary:
        lines.append(f'**{summary}**')

    lines.append('')
    lines.append('---')
    lines.append('')

    # 1. Stack
    if info:
        lines.append('## Stack do Projeto')
        lines.append('')
        lines.append(build_stack_table(info))
        lines.append('')

    # 2. Estrutura de Pacotes
    lines.append('## Estrutura de Pacotes')
    lines.append('')
    lines.append(f'Pacote base: `{base_pkg}`')
    lines.append('')
    if package_structure:
        lines.append('Módulos identificados:')
        lines.append('')
        lines.append(package_structure)
    else:
        lines.append('*Módulos a definir durante a implementação*')
    lines.append('')

    # 3. Exemplos de Classes (se disponível)
    if examples:
        lines.append(build_class_examples_section(examples))
        lines.append('')

    # 4. Requisitos
    lines.append('## Requisitos')
    lines.append('')

    objetivo = get_custom_field(jira_data, 'Objetivo')
    if objetivo:
        lines.append(f'**Objetivo:** {objetivo}')
        lines.append('')

    if custom_text:
        # Resumo estruturado dos requisitos - primeiros 400 chars
        clean_text = custom_text.strip()[:800]
        lines.append('**Requisitos Funcionais (resumo):**')
        lines.append('')
        lines.append(clean_text)
        lines.append('')

    # 5. Entidades/Domínios
    if entities:
        lines.append(build_entity_table(entities))
        lines.append('')

    # 6. Subtarefas
    lines.append('## Subtarefas')
    lines.append('')
    lines.append(build_task_table(tasks))
    lines.append('')

    # 7. Endpoints Planejados
    if endpoints:
        lines.append('## Endpoints Planejados')
        lines.append('')
        lines.append(build_endpoint_table(endpoints))
        lines.append('')

    # 8. Dependências
    lines.append('## Dependências entre Tasks')
    lines.append('')
    lines.append('```')
    lines.append(build_dependency_diagram(tasks))
    lines.append('```')
    lines.append('')

    # 9. Riscos
    lines.append('## Riscos')
    lines.append('')
    lines.append(build_risks_table(jira_data, keywords))
    lines.append('')

    # 10. Observações finais
    lines.append('---')
    lines.append('')
    lines.append(f'*Plano gerado automaticamente em {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')
    lines.append('*Revise e ajuste conforme necessário antes de iniciar a implementação.*')
    lines.append('')

    output = '\n'.join(lines)

    output_file = os.path.join(ticket_dir, 'implementation-plan.md')
    with open(output_file, 'w') as f:
        f.write(output)

    print(f"[PLAN] implementation-plan.md gerado em {output_file}", file=sys.stderr)


if __name__ == '__main__':
    main()
