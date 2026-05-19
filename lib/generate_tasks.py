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
    # Procurar de baixo pra cima a partir do ticket_dir
    for d in [ticket_dir, os.path.dirname(ticket_dir),
              os.path.dirname(os.path.dirname(ticket_dir)),
              os.path.dirname(os.path.dirname(os.path.dirname(ticket_dir)))]:
        if not d or d == '/':
            break
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


# ---------------------------------------------------------------------------
# Geracao de tasks por linguagem
# ---------------------------------------------------------------------------

def java_tasks(config, scan_data, jira_data, keywords, ticket_id):
    """Gera tasks para projetos Java/Spring."""
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

    # --- Task 1: Modelo de dados ---
    if keywords.get('needs_model', True):
        tasks.append(dict(**K, id=nid(),
            descricao=f"Criar entidade, DTOs e repository JPA para {domain}",
            nivel='junior',
            observacoes=(
                f"Pacote base: {pkg}\n"
                f"Criar:\n"
                f"  1. Entidade JPA (@Entity, @Table, @Id, @GeneratedValue)\n"
                f"  2. DTOs de request/response\n"
                f"  3. Repository (Spring Data JPA)\n\n"
                f"Seguir padroes existentes no pacote {pkg}\n"
                f"[Junior] Veja entidades existentes como referencia de anotacoes"
            ),
            tipo='criar-classe', dependeDe=[]))

    model_id = tasks[-1]['id'] if tasks else None

    # --- Task 2: Servico + Endpoint ---
    if keywords.get('needs_api', True):
        deps = [model_id] if model_id else []
        tasks.append(dict(**K, id=nid(),
            descricao=f"Criar servico com regras de negocio e endpoint REST para {domain}",
            nivel='pleno',
            observacoes=(
                f"Pacote servico: {pkg}.service\n"
                f"Pacote controller: {pkg}.controller\n\n"
                f"Implementar CRUD completo:\n"
                f"  - listar, incluir, editar, excluir\n\n"
                f"Validacoes:\n"
                f"  - Validar campos obrigatorios\n"
                f"  - Tratar erros com ResponseEntity\n\n"
                f"[Pleno] Seguir padrao de ResponseDTO dos controllers existentes\n"
                f"Usar @RequiredArgsConstructor, @Valid nos request bodies"
            ),
            tipo='implementar', dependeDe=deps))

    api_id = tasks[-1]['id'] if tasks else None

    # --- Task 3: Validacao extra (se necessario) ---
    if keywords.get('needs_validation') and api_id:
        tasks.append(dict(**K, id=nid(),
            descricao=f"Criar servico de validacao para regras de negocio de {domain}",
            nivel='pleno',
            observacoes=(
                f"Pacote: {pkg}.service\n\n"
                f"Implementar validacoes especificas:\n"
                f"  - Regras de bloqueio conforme requisitos\n"
                f"  - Excecoes semanticas por tipo de erro\n\n"
                f"[Pleno] Integrar com o servico existente via injecao de dependencia"
            ),
            tipo='criar-classe', dependeDe=[api_id]))

    # --- Task 4: Processamento/Calculo (se necessario) ---
    if keywords.get('needs_calculation') and api_id:
        tasks.append(dict(**K, id=nid(),
            descricao=f"Implementar logica de processamento/calculo para {domain}",
            nivel='senior',
            observacoes=(
                f"Pacote: {pkg}.service\n\n"
                f"Implementar logica de negocio principal:\n"
                f"  - Algoritmo de calculo conforme requisitos\n"
                f"  - Atencao a regressao em funcionalidades existentes\n"
                f"  - Validar com casos reais antes de finalizar\n\n"
                f"[Senior] Esta e a task de maior risco tecnico"
            ),
            tipo='alterar-classe', dependeDe=[api_id]))

    calc_id = tasks[-1]['id'] if keywords.get('needs_calculation') and api_id else None

    # --- Task 5: Exportacao (se necessario) ---
    if keywords.get('needs_export') and (calc_id or api_id):
        tasks.append(dict(**K, id=nid(),
            descricao=f"Implementar exportacao/relatorios para {domain}",
            nivel='junior',
            observacoes=(
                "Formatos: CSV, PDF, XLS (conforme existentes no projeto)\n"
                "Seguir padrao de exportacao ja utilizado no projeto\n\n"
                "[Junior] Veja exemplos de exportacao em modulos similares"
            ),
            tipo='alterar-classe',
            dependeDe=[calc_id or api_id]))

    # --- Task 6: Testes ---
    test_deps = [t['id'] for t in tasks if t['tipo'] in ('implementar', 'criar-classe')]
    tasks.append(dict(**K, id=nid(),
        descricao=f"Escrever testes unitarios e de integracao para {domain}",
        nivel='pleno',
        observacoes=(
            "Testes unitarios:\n"
            "  - Cenarios de sucesso e erro para cada endpoint\n"
            "  - Validacao de regras de negocio\n"
            "Testes de integracao:\n"
            "  - Fluxo completo: entrada → processamento → saida\n"
            "Framework: JUnit + Mockito (ou equivalente no projeto)\n\n"
            "[Pleno/Junior] Pode ser dividido:\n"
            "  - Junior: cenarios basicos\n"
            "  - Pleno: fluxos de excecao e integracao"
        ),
        tipo='testes', dependeDe=test_deps))

    # --- Task 7: UI (se tiver frontend no config) ---
    test_id = tasks[-1]['id']

    # --- Task 8: Demo (sempre) ---
    demo_deps = [tasks[0]['id']] if tasks else []
    tasks.append(dict(**K, id=nid(),
        descricao=f"Preparar artefatos de demonstracao para {domain}",
        nivel='junior',
        observacoes=(
            "Artefatos:\n"
            "  - roteiro-demo.md: cenarios de apresentacao\n"
            "  - postman-collection.json: requests organizados\n"
            "  - postman-environment.json: variaveis de ambiente\n"
            "  - queries.sql: consultas SQL antes/depois\n\n"
            "[Junior] Antes de criar requests, leia os DTOs no codigo fonte\n"
            "Use valores realistas, nao invente campos"
        ),
        tipo='demo', dependeDe=demo_deps,
        artefatos=['roteiro-demo.md', 'postman-collection.json',
                   'postman-environment.json', 'queries.sql']))

    return tasks


def javascript_tasks(config, scan_data, jira_data, keywords, ticket_id):
    """Gera tasks para projetos JavaScript/React/Node."""
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

    # --- Task 1: Componentes de UI ---
    tasks.append(dict(**K, id=nid(),
        descricao=f"Criar componentes de UI para {domain}",
        nivel='junior',
        observacoes=(
            "Criar componentes seguindo padrao do projeto:\n"
            "  - Usar React hooks (useState, useEffect)\n"
            "  - Seguir estrutura de pastas existente\n"
            "  - Styled Components / CSS Modules conforme projeto\n\n"
            "[Junior] Veja componentes similares como referencia"
        ),
        tipo='criar-classe', dependeDe=[]))

    # --- Task 2: Servico/API ---
    tasks.append(dict(**K, id=nid(),
        descricao=f"Criar servico de API e hooks para {domain}",
        nivel='pleno',
        observacoes=(
            "Criar servico de comunicacao com API:\n"
            "  - Chamadas HTTP (fetch/axios conforme projeto)\n"
            "  - Tratamento de erros e loading states\n"
            "  - Custom hooks para reutilizacao\n\n"
            "[Pleno] Seguir padrao de servicos existentes"
        ),
        tipo='implementar', dependeDe=[tasks[0]['id']]))

    # --- Task 3: Pagina/Feature completa ---
    tasks.append(dict(**K, id=nid(),
        descricao=f"Implementar pagina completa de {domain}",
        nivel='senior',
        observacoes=(
            "Implementar a feature completa:\n"
            "  - Integracao componentes + servico\n"
            "  - Estado global (se aplicavel)\n"
            "  - Navegacao e rotas\n"
            "  - Testes (Jest/React Testing Library)\n\n"
            "[Senior] Garantir consistencia com o design system do projeto"
        ),
        tipo='implementar', dependeDe=[tasks[-1]['id']]))

    # --- Task 4: Testes ---
    tasks.append(dict(**K, id=nid(),
        descricao=f"Escrever testes para {domain}",
        nivel='pleno',
        observacoes=(
            "Testes com framework do projeto (Jest, Vitest, etc.):\n"
            "  - Testes de renderizacao dos componentes\n"
            "  - Testes de servico/API (mock)\n"
            "  - Testes de integracao (Cypress/Playwright se houver)\n\n"
            "[Pleno/Junior] Pode ser dividido entre membros do time"
        ),
        tipo='testes', dependeDe=[t['id'] for t in tasks if t['tipo'] == 'implementar']))

    # --- Task 5: Demo ---
    tasks.append(dict(**K, id=nid(),
        descricao=f"Preparar demonstracao de {domain}",
        nivel='junior',
        observacoes="Roteiro de demonstracao funcional da interface implementada",
        tipo='demo', dependeDe=[tasks[-2]['id']],
        artefatos=['roteiro-demo.md']))

    return tasks


def generic_tasks(config, scan_data, jira_data, keywords, ticket_id):
    """Gera tasks genericas para linguagens nao mapeadas."""
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
        descricao=f"Analisar requisitos e planejar implementacao de {domain}",
        nivel='pleno',
        observacoes=(
            "Ler atentamente os requisitos funcionais e tecnicos.\n"
            "Mapear arquivos e modulos afetados no projeto."
        ),
        tipo='analise', dependeDe=[]))

    tasks.append(dict(**K, id=nid(),
        descricao=f"Implementar funcionalidade de {domain}",
        nivel='senior',
        observacoes="Implementar conforme especificacao e padroes do projeto",
        tipo='implementar', dependeDe=[tasks[0]['id']]))

    tasks.append(dict(**K, id=nid(),
        descricao=f"Escrever testes para {domain}",
        nivel='pleno',
        observacoes="Testes unitarios e de integracao conforme framework do projeto",
        tipo='testes', dependeDe=[tasks[-1]['id']]))

    tasks.append(dict(**K, id=nid(),
        descricao=f"Preparar demonstracao de {domain}",
        nivel='junior',
        observacoes="Roteiro de demonstracao",
        tipo='demo', dependeDe=[tasks[-2]['id']]))

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
