#!/usr/bin/env python3
"""Gera status-tasks.json a partir dos dados Jira, scan de codigo e config.

Uso: python3 generate-tasks.py TICKET_DIR [CONFIG_FILE]
  - Le: TICKET_DIR/jira-data.json, TICKET_DIR/impact-report.json
  - Le: CONFIG_FILE (opcional, auto-descoberto)
  - Gera: TICKET_DIR/status-tasks.json
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def find_config(ticket_dir):
    """Auto-descobre refine-config.local.json ou refine-config.json."""
    ticket_dir = os.path.abspath(ticket_dir)
    # Procurar de baixo pra cima a partir do ticket_dir
    parts = ticket_dir.split(os.sep)
    for depth in range(len(parts), 0, -1):
        d = os.sep.join(parts[:depth]) or '/'
        for name in ['refine-config.local.json', 'refine-config.json']:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def get_custom_field(jira_data, name):
    for v in jira_data.get('customFields', {}).values():
        if isinstance(v, dict) and v.get('name') == name:
            return v.get('value', '')
    return ''


def get_change_keywords(jira_data):
    """Extrai palavras-chave do ticket para orientar a geracao de tasks."""
    text = ' '.join(filter(None, [
        jira_data.get('basic', {}).get('summary', ''),
        get_custom_field(jira_data, 'Objetivo'),
        get_custom_field(jira_data, 'Requisitos Funcionais'),
        get_custom_field(jira_data, 'Requisitos de Interface'),
    ]))
    text_lower = text.lower()
    kw = {
        'is_new': bool(re.search(r'criar|novo|nova|cadastr|adicionar', text_lower)),
        'is_modify': bool(re.search(r'alter|modific|ajust|adapt|mudan', text_lower)),
        'needs_model': bool(re.search(r'entidade|tabela|banco|dados.*persist', text_lower)),
        'needs_api': bool(re.search(r'endpoint|api|rest|controller|serviço|servico', text_lower)),
        'needs_validation': bool(re.search(r'validar|validação|validacao|regra|bloque', text_lower)),
        'needs_calculation': bool(re.search(r'calcular|cálculo|calculo|processamento|calcular', text_lower)),
        'needs_ui': bool(re.search(r'tela|modal|formulário|formulario|front|página|pagina|componente', text_lower)),
        'needs_export': bool(re.search(r'exportar|exportação|exportacao|relatório|relatorio|csv|pdf|xls', text_lower)),
        'needs_test': True,  # sempre precisa de teste
    }
    return kw


def detect_base_package(scan_data):
    """Detecta o pacote base a partir do scan."""
    if not scan_data:
        return 'com.exemplo.projeto'
    packages = scan_data.get('packages', [])
    if not packages:
        return 'com.exemplo.projeto'
    # packages pode ser array de strings (ex: ["com.maps.dataa", ...])
    # Pega o primeiro como base
    if isinstance(packages, list):
        longest = max(packages, key=len) if packages else 'com.exemplo'
        parts = longest.split('.')
        if len(parts) >= 4:
            return '.'.join(parts[:4])
        return '.'.join(parts[:3]) if len(parts) >= 3 else longest
    # Se for dict (nome -> count)
    if isinstance(packages, dict):
        sorted_pkgs = sorted(packages.items(), key=lambda x: -x[1])
        if sorted_pkgs:
            top = sorted_pkgs[0][0]
            parts = top.split('.')
            if len(parts) >= 4:
                return '.'.join(parts[:4])
            return '.'.join(parts[:3]) if len(parts) >= 3 else top
    return 'com.exemplo.projeto'


def summarize_domain(text, max_words=4):
    """Extrai palavras-chave do dominio do texto."""
    if not text:
        return 'funcionalidade'
    # Tenta palavras com inicial maiuscula (dominio em PT/EN)
    words = re.findall(r'[A-Z][a-záéíóúâêôãçà-ü]{2,}', text)
    if words:
        return ' '.join(words[:max_words])
    # Fallback: primeiras palavras significativas (>=4 chars, nao artigos)
    all_words = re.findall(r'\b[a-zA-Záéíóúâêôãçà-ü]{4,}\b', text)
    stopwords = {'para', 'com', 'que', 'dos', 'das', 'por', 'mas', 'como', 'mais', 'uma', 'seu'}
    filtered = [w for w in all_words if w.lower() not in stopwords]
    if filtered:
        return ' '.join(filtered[:max_words]).title()
    return 'funcionalidade'


def extract_project_conventions(scan_data):
    """Extrai convencoes do projeto a partir do scan de documentacao."""
    docs = (scan_data or {}).get('projectDocs', {})
    if not docs:
        return ''

    lines = []
    found = False

    # README.md - extrair nome do projeto
    readme = docs.get('readme', '')
    if readme:
        for line in readme.split('\n'):
            line = line.strip()
            if line.startswith('# ') and len(line) > 3:
                lines.append(f"Projeto: {line[2:].strip()}")
                found = True
                break

    # Exemplos de classes do projeto
    examples = {}
    for key, label in [('controllerExamples', 'Controller'),
                       ('serviceExamples', 'Service'),
                       ('entityExamples', 'Entity')]:
        vals = docs.get(key, [])
        if vals and isinstance(vals, list):
            examples[label] = [v.split('/')[-1] for v in vals[:3]]

    if examples:
        found = True
        lines.append("Exemplos de classes no projeto:")
        for label, names in examples.items():
            lines.append(f"  - {label}: {', '.join(names)}")

    # SDDs
    sdds = docs.get('sdds', [])
    if sdds and isinstance(sdds, list) and sdds:
        found = True
        lines.append(f"SDDs encontrados: {len(sdds)} arquivo(s)")
        for s in sdds[:3]:
            lines.append(f"  - {s}")

    # AGENTS.md
    agents = docs.get('agents', '')
    if agents:
        found = True
        # Extrair primeiras linhas nao vazias
        non_empty = [l.strip() for l in agents.split('\n') if l.strip()]
        if non_empty:
            preview = ' | '.join(non_empty[:2])
            lines.append(f"AGENTS.md: {preview[:120]}")

    if not found:
        return ''

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Geracao de tasks por linguagem
# ---------------------------------------------------------------------------

def java_tasks(config, scan_data, jira_data, keywords, ticket_id):
    """Gera tasks verticais consolidadas para projetos Java/Spring.

    Cada task agrupa tudo necessario para entregar um incremento testado:
      1. CRUD completo (junior/pleno): entidade + DTOs + repository +
         servico + endpoint + validacoes + exportacao + testes
      2. Logica de processamento (senior, opcional): regras de negocio
         complexas, calculos, arredondamento
      3. Artefatos de demo (junior): roteiro + Postman + queries
    """
    tasks = []
    task_id = [0]
    def nid():
        task_id[0] += 1
        return f"{task_id[0]:04d}"

    K = dict(projeto=config['name'], caminhoProjeto=config['path'],
             bloqueadoPor=None, status='pendente')

    pkg = detect_base_package(scan_data)
    domain = summarize_domain(
        jira_data.get('basic', {}).get('summary', '') + ' ' +
        get_custom_field(jira_data, 'Objetivo')
    )

    change_type = ''
    text = ' '.join(filter(None, [
        jira_data.get('basic', {}).get('summary', ''),
        get_custom_field(jira_data, 'Objetivo'),
    ])).lower()
    if re.search(r'parametro|parametriza|config|casa.*decimal|arredondamento', text):
        change_type = 'parametrizacao'
    elif re.search(r'criar|novo|nova|cadastr|adicionar', text):
        change_type = 'criacao'
    else:
        change_type = 'alteracao'

    precisa_export = keywords.get('needs_export', False)
    precisa_calculo = keywords.get('needs_calculation', False)

    # Extrair convencoes do projeto para enriquecer observacoes
    project_conventions = extract_project_conventions(scan_data)

    # ------------------------------------------------------------------
    # Task 1 — CRUD completo + validacoes + exportacao + testes
    # ------------------------------------------------------------------
    desc_crud = f"Implementar CRUD completo de {domain}"
    if precisa_export:
        desc_crud += " com exportacao/relatorios"

    obs_crud = (
        f"Pacote base: {pkg}\n\n"
        f"Criar/alterar:\n"
        f"  1. Entidade JPA + DTOs de request/response\n"
        f"  2. Repository (Spring Data JPA)\n"
        f"  3. Servico com regras de negocio e validacoes\n"
        f"  4. Controller REST (CRUD completo)\n"
    )
    if precisa_export:
        obs_crud += (
            f"  5. Exportacao (CSV, PDF, XLS conforme padrao do projeto)\n"
        )
    obs_crud += (
        f"\nTestes (obrigatorios):\n"
        f"  - Unitarios: cenarios de sucesso e erro para cada endpoint\n"
        f"  - Integracao: fluxo completo (entrada → banco → saida)\n"
        f"  Framework: JUnit + Mockito (ou equivalente no projeto)\n\n"
        f"[Junior/Pleno] Siga os padroes existentes no pacote {pkg}\n"
        f"Veja controllers, services e entidades similares como referencia\n"
        f"Use @RequiredArgsConstructor, @Valid, ResponseEntity"
    )
    if project_conventions:
        obs_crud += f"\n\n--- Contexto do Projeto ---\n{project_conventions}"

    tasks.append(dict(**K, id=nid(),
        descricao=desc_crud,
        nivel='junior',
        observacoes=obs_crud,
        tipo='implementar', dependeDe=[]))

    # ------------------------------------------------------------------
    # Task 2 — Logica de processamento (opcional, se houver calculo)
    # ------------------------------------------------------------------
    if precisa_calculo:
        obs_calculo = (
            f"Pacote: {pkg}.service\n\n"
            f"Implementar a logica de negocio principal:\n"
            f"  - Algoritmo de calculo conforme requisitos\n"
            f"  - Arredondamento e precisao numerica\n"
            f"  - Atencao a regressao em funcionalidades existentes\n\n"
            f"Testes (obrigatorios):\n"
            f"  - Unitarios: cenario de calculo com valores conhecidos\n"
            f"  - Comparacao com resultados esperados (casos reais)\n\n"
            f"[Senior] Esta e a task de maior risco tecnico.\n"
            f"Valide com casos reais antes de finalizar"
        )
        if project_conventions:
            obs_calculo += f"\n\n--- Contexto do Projeto ---\n{project_conventions}"
        tasks.append(dict(**K, id=nid(),
            descricao=f"Implementar logica de processamento/calculo de {domain}",
            nivel='senior',
            observacoes=obs_calculo,
            tipo='alterar-classe',
            dependeDe=[tasks[0]['id']]))

    # ------------------------------------------------------------------
    # Task 3 — Artefatos de demo (sempre)
    # ------------------------------------------------------------------
    tasks.append(dict(**K, id=nid(),
        descricao=f"Preparar artefatos de demonstracao de {domain}",
        nivel='junior',
        observacoes=(
            "Artefatos:\n"
            "  - roteiro-demo.md: cenarios de apresentacao para o negocio\n"
            "  - postman-collection.json: requests organizados por cenario\n"
            "  - postman-environment.json: variaveis de ambiente\n"
            "  - queries.sql: consultas SQL antes/depois\n\n"
            "[Junior] Antes de criar requests, leia os DTOs no codigo fonte\n"
            "Use valores realistas baseados nos DTOs - nunca invente campos"
        ),
        tipo='demo', dependeDe=[tasks[0]['id']],
        artefatos=['roteiro-demo.md', 'postman-collection.json',
                   'postman-environment.json', 'queries.sql']))

    return tasks


def javascript_tasks(config, scan_data, jira_data, keywords, ticket_id):
    """Gera tasks verticais consolidadas para projetos JS/React/Node.

    Cada task agrupa implementacao + testes:
      1. Feature completa (junior/pleno/senior): componentes + servico +
         estado + testes
      2. Artefatos de demo (junior)
    """
    tasks = []
    task_id = [0]
    def nid():
        task_id[0] += 1
        return f"{task_id[0]:04d}"

    K = dict(projeto=config['name'], caminhoProjeto=config['path'],
             bloqueadoPor=None, status='pendente')

    domain = summarize_domain(
        jira_data.get('basic', {}).get('summary', '') + ' ' +
        get_custom_field(jira_data, 'Objetivo')
    )

    # --- Task 1: Feature completa (componentes + servico + estado + testes) ---
    tasks.append(dict(**K, id=nid(),
        descricao=f"Implementar feature completa de {domain}",
        nivel='pleno',
        observacoes=(
            "Implementar a feature de ponta a ponta:\n"
            "  1. Componentes de UI (React, hooks, estado)\n"
            "  2. Servico de API (fetch/axios, tratamento de erros)\n"
            "  3. Integracao componentes + servico\n"
            "  4. Navegacao e rotas\n\n"
            "Testes (obrigatorios):\n"
            "  - Renderizacao dos componentes\n"
            "  - Servico/API com mock\n"
            "  - Integracao (Cypress/Playwright se houver)\n"
            "  Framework: Jest/Vitest conforme projeto\n\n"
            "[Pleno] Siga o design system e estrutura de pastas existente"
        ),
        tipo='implementar', dependeDe=[]))

    # --- Task 2: Artefatos de demo ---
    tasks.append(dict(**K, id=nid(),
        descricao=f"Preparar demonstracao de {domain}",
        nivel='junior',
        observacoes="Roteiro de demonstracao funcional da interface implementada",
        tipo='demo', dependeDe=[tasks[0]['id']],
        artefatos=['roteiro-demo.md']))

    return tasks


def generic_tasks(config, scan_data, jira_data, keywords, ticket_id):
    """Gera tasks verticais consolidadas para linguagens nao mapeadas.

    Cada task agrupa implementacao + testes:
      1. Implementar funcionalidade (pleno/senior)
      2. Artefatos de demo (junior)
    """
    tasks = []
    task_id = [0]
    def nid():
        task_id[0] += 1
        return f"{task_id[0]:04d}"

    K = dict(projeto=config['name'], caminhoProjeto=config['path'],
             bloqueadoPor=None, status='pendente')

    domain = summarize_domain(
        jira_data.get('basic', {}).get('summary', '') + ' ' +
        get_custom_field(jira_data, 'Objetivo')
    )

    tasks.append(dict(**K, id=nid(),
        descricao=f"Implementar funcionalidade de {domain}",
        nivel='pleno',
        observacoes=(
            "Implementar conforme especificacao e padroes do projeto.\n\n"
            "Testes (obrigatorios):\n"
            "  - Unitarios: cenarios de sucesso e erro\n"
            "  - Integracao: fluxo completo\n"
            "  Framework conforme padrao do projeto\n\n"
            "[Pleno] Analise os requisitos antes de implementar"
        ),
        tipo='implementar', dependeDe=[]))

    tasks.append(dict(**K, id=nid(),
        descricao=f"Preparar demonstracao de {domain}",
        nivel='junior',
        observacoes="Roteiro de demonstracao",
        tipo='demo', dependeDe=[tasks[0]['id']]))

    return tasks


LANGUAGE_HANDLERS = {
    'java': java_tasks,
    'javascript': javascript_tasks,
    'typescript': javascript_tasks,
    'node': javascript_tasks,
    'react': javascript_tasks,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Uso: generate-tasks.py TICKET_DIR [CONFIG_FILE]", file=sys.stderr)
        sys.exit(1)

    ticket_dir = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else find_config(ticket_dir)

    if not config_file:
        print("[TASKS] ERRO: refine-config.local.json nao encontrado", file=sys.stderr)
        # Fallback: usar dados do scan
        config_file = None

    config = load_json(config_file) if config_file else {}
    jira_data = load_json(os.path.join(ticket_dir, 'jira-data.json'))

    if not jira_data:
        print("[TASKS] ERRO: jira-data.json nao encontrado", file=sys.stderr)
        sys.exit(1)

    ticket_id = jira_data.get('ticketId', 'DESCONHECIDO')
    keywords = get_change_keywords(jira_data)
    projects = (config.get('projects', []) if config
                else [{'name': 'projeto', 'path': '../projeto',
                       'language': 'java', 'buildTool': 'unknown'}])

    if not projects:
        print("[TASKS] Nenhum projeto configurado", file=sys.stderr)
        sys.exit(1)

    all_tasks = []
    ticket_projects = []

    for proj in projects:
        proj_name = proj.get('name', 'projeto')
        lang = proj.get('language', 'java')
        scan_file = os.path.join(ticket_dir, 'impact-report.json')
        scan_data = load_json(scan_file)

        # Se o scan tem multiplos projetos, encontrar o correto
        if isinstance(scan_data, list):
            scan_proj = next((p for p in scan_data if p.get('name') == proj_name), None)
            if not scan_proj:
                scan_proj = scan_data[0]  # fallback
            scan_data = scan_proj

        handler = LANGUAGE_HANDLERS.get(lang, generic_tasks)
        proj_tasks = handler(proj, scan_data, jira_data, keywords, ticket_id)

        # Remover prefixo numerico para permitir juncao
        for i, t in enumerate(proj_tasks):
            t['projeto'] = proj_name
            t['caminhoProjeto'] = proj.get('path', '../projeto')
            # Preservar nivel se o handler nao definiu
            if 'nivel' not in t:
                t['nivel'] = 'pleno'

        all_tasks.extend(proj_tasks)
        ticket_projects.append(proj_name)

    # Renumerar tasks
    for i, t in enumerate(all_tasks):
        t['id'] = f"{i+1:04d}"

    if not all_tasks:
        print("[TASKS] Nenhuma task gerada", file=sys.stderr)
        sys.exit(0)

    output = {
        'ticketId': ticket_id,
        'ultimaAtualizacao': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'projetosEnvolvidos': ticket_projects,
        'tarefas': all_tasks,
    }

    output_file = os.path.join(ticket_dir, 'status-tasks.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[TASKS] {len(all_tasks)} tarefas geradas em {output_file}", file=sys.stderr)


if __name__ == '__main__':
    main()
