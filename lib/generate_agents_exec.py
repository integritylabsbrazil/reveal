#!/usr/bin/env python3
"""Gera AGENTS-EXEC.md com instrucoes de execucao por task.

Uso: python3 generate_agents_exec.py TICKET_DIR
"""

import json
import os
import re
import sys
from datetime import datetime


def _name_to_class(name):
    """Converte nome para PascalCase."""
    trans = str.maketrans({
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'Ç': 'C',
    })
    clean = name.translate(trans)
    parts = clean.replace('_', ' ').split()
    return ''.join(p.capitalize() for p in parts if p)


def _field_name(name):
    """Converte para camelCase."""
    trans = str.maketrans({
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'Ç': 'C',
        ' ': '_',
    })
    clean = name.translate(trans).lower()
    parts = clean.split('_')
    result = parts[0]
    for p in parts[1:]:
        if p:
            result += p[0].upper() + p[1:]
    return result


def extract_domain(text):
    """Extrai nome do dominio de uma descricao de task."""
    m = re.search(r'de\s+(.+?)(?:\s+(?:com|em|no|na|para|e|\(|\s*$))', text)
    if m:
        return m.group(1).strip()
    return 'funcionalidade'


def generate_agents_exec(ticket_dir):
    with open(os.path.join(ticket_dir, 'status-tasks.json')) as f:
        data = json.load(f)

    ticket_id = data.get('ticketId', 'DESCONHECIDO')
    tasks = data.get('tarefas', [])
    projetos = data.get('projetosEnvolvidos', [])

    lines = []
    lines.append(f'# Execução — {ticket_id}')
    lines.append('')
    lines.append(f'Instrucoes diretas para o agente implementar cada task.')
    lines.append('')
    lines.append('---')
    lines.append('')

    for t in tasks:
        tid = t['id']
        desc = t.get('descricao', '')
        tipo = t.get('tipo', '')
        nivel = t.get('nivel', '')
        deps = t.get('dependeDe', [])
        jira_key = t.get('jiraKey', '')
        projeto = t.get('projeto', 'projeto')
        caminho = t.get('caminhoProjeto', '../projeto')

        domain = extract_domain(desc)
        class_name = _name_to_class(domain)
        entity_var = _field_name(class_name) if class_name else 'entity'

        lines.append(f'## Task {tid} — {desc}')
        lines.append('')
        if jira_key:
            lines.append(f'**Jira:** {jira_key}')
        lines.append(f'**Nivel:** {nivel}')
        lines.append(f'**Tipo:** {tipo}')
        lines.append(f'**Projeto:** {projeto} ({caminho})')
        if deps:
            lines.append(f'**Depende de:** task(s) {", ".join(deps)} concluida(s)')
        lines.append('')

        if tipo == 'implementar':
            lines.append('### Arquivos a criar')
            lines.append('')
            lines.append(f'1. Migration Liquibase — `src/main/resources/db/changelog/.../migration.xml`')
            lines.append(f'2. Entity — `src/main/java/.../domain/{class_name}.java`')
            lines.append(f'3. DTO Input — `src/main/java/.../model/{class_name}Input.java`')
            lines.append(f'4. DTO Output — `src/main/java/.../model/{class_name}Output.java`')
            lines.append(f'5. Repository — `src/main/java/.../repository/{class_name}Repository.java`')
            lines.append(f'6. Service — `src/main/java/.../service/{class_name}Service.java`')
            lines.append(f'7. Controller — `src/main/java/.../controller/{class_name}Controller.java`')
            lines.append('')
            lines.append('### Referencias no projeto')
            lines.append('')
            lines.append(f'- Ler entidades similares em `{caminho}/src/main/java/.../domain/`')
            lines.append(f'- Ler services existentes em `{caminho}/src/main/java/.../service/`')
            lines.append(f'- Ler controllers existentes em `{caminho}/src/main/java/.../controller/`')
            lines.append('')
            lines.append(f'### Comandos')
            lines.append('')
            lines.append('```bash')
            lines.append(f'cd {caminho}')
            lines.append('mvn compile')
            lines.append('mvn test')
            lines.append('```')
            lines.append('')

        elif tipo == 'alterar-classe':
            lines.append('### Arquivos a modificar')
            lines.append('')
            lines.append(f'- Localizar classes existentes no pacote do projeto `{caminho}`')
            lines.append(f'- Identificar services, validators e actions relacionados a `{domain}`')
            lines.append(f'- Adicionar/alterar logica mantendo compatibilidade com codigo existente')
            lines.append('')
            lines.append('### Comandos')
            lines.append('')
            lines.append('```bash')
            lines.append(f'cd {caminho}')
            lines.append('mvn compile')
            lines.append('mvn test')
            lines.append('```')
            lines.append('')

        elif tipo == 'demo':
            lines.append('### Artefatos a gerar')
            lines.append('')
            lines.append('- roteiro-demo.md com cenarios de apresentacao')
            lines.append('- postman-collection.json com requests organizados')
            lines.append('- postman-environment.json com variaveis')
            lines.append('- queries.sql para validacao antes/depois')
            lines.append('')
            lines.append('Antes de criar requests, leia os DTOs no codigo fonte.')
            lines.append('Use valores realistas - nunca invente campos.')
            lines.append('')

        lines.append('### Commit')
        lines.append('')
        lines.append('```bash')
        lines.append(f'git add .')
        lines.append(f'git commit -m "{ticket_id}-{tid}: {desc[:72]}"')
        lines.append('```')
        lines.append('')
        lines.append('---')
        lines.append('')

    lines.append('')
    lines.append(f'*Gerado em {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')

    output = '\n'.join(lines)
    output_file = os.path.join(ticket_dir, 'AGENTS-EXEC.md')
    with open(output_file, 'w') as f:
        f.write(output)
    print(f'[EXEC] AGENTS-EXEC.md gerado ({len(output)} bytes)', file=sys.stderr)
    return output


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: generate_agents_exec.py TICKET_DIR', file=sys.stderr)
        sys.exit(1)
    generate_agents_exec(sys.argv[1])
