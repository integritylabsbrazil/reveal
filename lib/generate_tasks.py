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

sys.path.insert(0, os.path.dirname(__file__))
from utils import load_json, get_custom_field, detect_base_package


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def suggest_granularity(keywords, jira_data, scan_data):
    """Sugere a granularidade ideal baseada na complexidade do ticket.
    
    Retorna: ('grossa'|'media'|'fina', motivo)
    """
    score = 0
    
    # Contar keywords ativas
    active_kw = [k for k, v in keywords.items() if v and k != 'needs_test']
    score += len(active_kw)
    
    # Pesos especiais
    if keywords.get('needs_calculation'):
        score += 2  # logica complexa aumenta granularidade
    if keywords.get('needs_ui'):
        score += 1
    if keywords.get('needs_export'):
        score += 1
    
    # Tipo de issue
    issuetype = (jira_data.get('basic', {}) or {}).get('issuetype', '')
    if issuetype.lower() in ('bug', 'hotfix'):
        score -= 1  # bugs tendem a ser mais simples
    
    # Quantidade de arquivos afetados (do scan)
    if scan_data:
        files = scan_data.get('files', []) or []
        controllers = sum(1 for f in files if f.get('type') == 'controller')
        services = sum(1 for f in files if f.get('type') == 'service')
        if controllers > 3 or services > 3:
            score += 1  # muitos arquivos = mais complexo
    
    # Decidir granularidade
    if score <= 3:
        return ('grossa', f'Pontuacao {score}/10: ticket simples, 3 tasks sao suficientes')
    elif score <= 6:
        return ('media', f'Pontuacao {score}/10: complexidade media, 6-7 tasks recomendadas')
    else:
        return ('fina', f'Pontuacao {score}/10: ticket complexo, 10-11 tasks recomendadas')


def load_project_context(project_name, script_dir):
    """Carrega o contexto permanente de um projeto a partir de projects-context/.
    
    Retorna dict com informacoes extraidas do arquivo projects-context/<projeto>.md,
    ou None se o arquivo nao existir.
    """
    context_dir = os.path.join(os.path.dirname(script_dir), 'projects-context') if os.path.isfile(script_dir) else os.path.join(script_dir, 'projects-context')
    if not os.path.isdir(context_dir):
        # Tentar encontrar de outras formas
        for candidate in [
            os.path.join(script_dir, '..', 'projects-context'),
            os.path.join(script_dir, 'projects-context'),
        ]:
            candidate = os.path.abspath(candidate)
            if os.path.isdir(candidate):
                context_dir = candidate
                break
        if not os.path.isdir(context_dir):
            return None
    
    ctx_file = os.path.join(context_dir, f'{project_name}.md')
    if not os.path.isfile(ctx_file):
        return None
    
    with open(ctx_file, 'r', errors='ignore') as f:
        content = f.read()
    
    # Extrair secoes do markdown
    result = {
        'raw': content,
        'controllers': [],
        'services': [],
        'entities': [],
        'packages': [],
        'conventions': '',
    }
    
    # Extrair nomes de classes Controller/Service/Entity
    for pattern, key in [
        (r'Controller:\s*(\S+)\.java', 'controllers'),
        (r'- Controller:\s*(\S+)', 'controllers'),
        (r'Service:\s*(\S+)\.java', 'services'),
        (r'- Service:\s*(\S+)', 'services'),
        (r'Entity:\s*(\S+)\.java', 'entities'),
        (r'- Entity:\s*(\S+)', 'entities'),
    ]:
        for match in re.finditer(pattern, content):
            result[key].append(match.group(1))
    
    # Extrair pacotes base
    for match in re.finditer(r'Pacote base[:\s]+([\w.]+)', content):
        result['packages'].append(match.group(1))
    
    # Extrair anotacoes mencionadas
    annotations = set()
    for match in re.finditer(r'@(\w+)', content):
        annotations.add(match.group(1))
    result['annotations'] = sorted(annotations)
    
    return result


def enrich_observations(obs_text, project_context, task_type=None, domain_name=None):
    """Enriquece observacoes tecnicas com informacoes do contexto do projeto."""
    if not project_context:
        return obs_text
    
    enriched_parts = [obs_text]
    
    # Adicionar exemplos concretos do projeto se disponiveis
    examples = []
    if project_context.get('controllers'):
        examples.append(f"Controllers de referencia: {', '.join(project_context['controllers'][:3])}")
    if project_context.get('services'):
        examples.append(f"Services de referencia: {', '.join(project_context['services'][:3])}")
    if project_context.get('entities'):
        examples.append(f"Entities de referencia: {', '.join(project_context['entities'][:3])}")
    if project_context.get('packages'):
        examples.append(f"Pacotes base: {', '.join(project_context['packages'][:3])}")
    if project_context.get('annotations'):
        examples.append(f"Anotacoes usadas no projeto: {', '.join(project_context['annotations'][:8])}")
    
    if examples:
        enriched_parts.append('\n---\n### **Contexto do Projeto (projects-context)**')
        enriched_parts.extend([f'- {e}' for e in examples])
    
    return '\n'.join(enriched_parts)


def estimate_effort(tipo, nivel):
    """Estima esforco em horas para uma task baseado no tipo e nivel.
    
    Retorna dict com {horas, descricao}.
    """
    base = {
        'implementar': 8,
        'criar-classe': 4,
        'alterar-classe': 6,
        'testes': 4,
        'demo': 3,
        'adicionar-endpoint': 3,
        'configuracao': 2,
    }
    nivel_mult = {
        'junior': 1.5,
        'pleno': 1.0,
        'senior': 0.8,
    }
    
    horas_base = base.get(tipo, 4)
    mult = nivel_mult.get(nivel, 1.0)
    horas = max(1, round(horas_base * mult))
    
    if horas <= 3:
        desc = 'pequeno'
    elif horas <= 6:
        desc = 'medio'
    else:
        desc = 'grande'
    
    return {'horas': horas, 'descricao': f'{desc} (~{horas}h)'}


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

def java_tasks(config, scan_data, jira_data, keywords, ticket_id, granularity='grossa'):
    """Gera tasks verticais consolidadas para projetos Java/Spring.

    Args:
        granularity: 'grossa' (3 tasks), 'media' (6-7), 'fina' (10-11)
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

    precisa_export = keywords.get('needs_export', False)
    precisa_calculo = keywords.get('needs_calculation', False)
    project_conventions = extract_project_conventions(scan_data)

    task_list = []

    if granularity == 'grossa':
        # --- Task 1: CRUD completo ---
        desc = f"Implementar CRUD completo de {domain}"
        if precisa_export:
            desc += " com exportacao/relatorios"
        obs = (
            f"Pacote base: {pkg}\n\n"
            f"Criar/alterar:\n"
            f"  1. Entidade JPA + DTOs de request/response\n"
            f"  2. Repository (Spring Data JPA)\n"
            f"  3. Servico com regras de negocio e validacoes\n"
            f"  4. Controller REST (CRUD completo)\n"
        )
        if precisa_export:
            obs += f"  5. Exportacao (CSV, PDF, XLS conforme padrao do projeto)\n"
        obs += (
            f"\nTestes (obrigatorios):\n"
            f"  - Unitarios: cenarios de sucesso e erro para cada endpoint\n"
            f"  - Integracao: fluxo completo (entrada → banco → saida)\n"
            f"  Framework: JUnit + Mockito (ou equivalente no projeto)\n\n"
            f"[Junior/Pleno] Siga os padroes existentes no pacote {pkg}\n"
            f"Veja controllers, services e entidades similares como referencia\n"
            f"Use @RequiredArgsConstructor, @Valid, ResponseEntity"
        )
        if project_conventions:
            obs += f"\n\n--- Contexto do Projeto ---\n{project_conventions}"
        task_list.append(dict(**K, id=nid(),
            descricao=desc, nivel='junior', observacoes=obs,
            tipo='implementar', dependeDe=[]))

        # --- Task 2: Logica (condicional) ---
        if precisa_calculo:
            obs = (
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
                obs += f"\n\n--- Contexto do Projeto ---\n{project_conventions}"
            task_list.append(dict(**K, id=nid(),
                descricao=f"Implementar logica de processamento/calculo de {domain}",
                nivel='senior', observacoes=obs,
                tipo='alterar-classe',
                dependeDe=[task_list[0]['id']]))

        # --- Task 3: Demo ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Preparar artefatos de demonstracao de {domain}",
            nivel='junior', observacoes=(
                "Artefatos:\n"
                "  - roteiro-demo.md: cenarios de apresentacao para o negocio\n"
                "  - postman-collection.json: requests organizados por cenario\n"
                "  - postman-environment.json: variaveis de ambiente\n"
                "  - queries.sql: consultas SQL antes/depois\n\n"
                "[Junior] Antes de criar requests, leia os DTOs no codigo fonte\n"
                "Use valores realistas baseados nos DTOs - nunca invente campos"
            ),
            tipo='demo', dependeDe=[task_list[0]['id']],
            artefatos=['roteiro-demo.md', 'postman-collection.json',
                       'postman-environment.json', 'queries.sql']))

    elif granularity == 'media':
        # --- Task 1: Migration + Entity + Repository ---
        obs1 = (
            f"Pacote base: {pkg}\n\n"
            f"Criar:\n"
            f"  1. Migration Liquibase (criacao de tabela, sequence, indices)\n"
            f"  2. Entidade JPA com anotacoes @Entity @Table @SequenceGenerator\n"
            f"  3. Repository (Spring Data JPA) com metodos de busca\n"
            f"  4. Testes unitarios do repository\n\n"
            f"Siga os padroes de entidades existentes no projeto\n"
            f"Use @Data @Builder @AllArgsConstructor @NoArgsConstructor"
        )
        if project_conventions:
            obs1 += f"\n\n--- Contexto ---\n{project_conventions}"
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar entidade + migration + repository de {domain}",
            nivel='junior', observacoes=obs1,
            tipo='criar-classe', dependeDe=[]))

        # --- Task 2: DTOs + Mapper ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar DTOs (input/output/filter) + mapper de {domain}",
            nivel='junior', observacoes=(
                f"Criar:\n"
                f"  1. DTO de entrada (Input) com validacoes (@NotBlank, @NotNull, @Max)\n"
                f"  2. DTO de saida (Output) com campos de exibicao\n"
                f"  3. DTO de filtro (Filter) para consultas\n"
                f"  4. Mapper MapStruct (interface + implementacao)\n\n"
                f"Siga os padroes de DTOs existentes no projeto\n"
                f"Use @Data @Builder @NoArgsConstructor @AllArgsConstructor"),
            tipo='criar-classe', dependeDe=[task_list[0]['id']]))

        # --- Task 3: Service ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Implementar service + regras de negocio de {domain}",
            nivel='pleno', observacoes=(
                f"Criar:\n"
                f"  1. Service com regras de negocio e validacoes\n"
                f"  2. Actions (validator, get, save, delete) se houver padrao\n"
                f"  3. Tratamento de excecoes especificas do dominio\n\n"
                f"Testes:\n"
                f"  - Unitarios do service com mocks\n"
                f"  - Cenarios de sucesso, erro e validacao\n\n"
                f"Siga os padroes de services existentes no projeto\n"
                f"Use @Service @Slf4j @Transactional @RequiredArgsConstructor"),
            tipo='implementar', dependeDe=[task_list[1]['id']]))

        # --- Task 4: Controller ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar controller REST de {domain}",
            nivel='junior', observacoes=(
                f"Criar:\n"
                f"  1. Controller com endpoints CRUD\n"
                f"  2. Tratamento de respostas (ResponseEntity)\n"
                f"  3. Documentacao OpenAPI/Swagger se houver padrao\n\n"
                f"Testes:\n"
                f"  - Testes de integracao do controller (MockMvc)\n"
                f"  - Cenarios de sucesso, erro 400/404/500\n\n"
                f"Siga os padroes de controllers existentes no projeto\n"
                f"Use @RestController @RequestMapping @RequiredArgsConstructor"),
            tipo='adicionar-endpoint', dependeDe=[task_list[2]['id']]))

        # --- Task 5: Testes ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Implementar testes unitarios e de integracao de {domain}",
            nivel='junior', observacoes=(
                f"Testes obrigatorios:\n\n"
                f"Unitarios:\n"
                f"  - Repository (spring-boot-starter-test + H2)\n"
                f"  - Service (Mockito)\n"
                f"  - Controller (MockMvc)\n\n"
                f"Integracao:\n"
                f"  - Fluxo completo: HTTP → controller → service → repository → banco\n"
                f"  - Cenarios de contorno (erro, validacao, nao encontrado)\n\n"
                f"Cobertura minima: 80% das linhas do codigo novo"),
            tipo='testes', dependeDe=[task_list[3]['id']]))

        # --- Task 6: Logica (condicional) ---
        if precisa_calculo:
            obs = (
                f"Implementar a logica de negocio principal:\n"
                f"  - Algoritmo de calculo conforme requisitos\n"
                f"  - Arredondamento e precisao numerica\n\n"
                f"Testes:\n"
                f"  - Unitarios: cenario de calculo com valores conhecidos\n"
                f"  - Comparacao com resultados esperados (casos reais)\n\n"
                f"[Senior] Valide com casos reais antes de finalizar"
            )
            if project_conventions:
                obs += f"\n\n--- Contexto do Projeto ---\n{project_conventions}"
            task_list.append(dict(**K, id=nid(),
                descricao=f"Implementar logica de processamento/calculo de {domain}",
                nivel='senior', observacoes=obs,
                tipo='alterar-classe',
                dependeDe=[task_list[4]['id']]))

        # --- Task 7: Demo ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Preparar artefatos de demonstracao de {domain}",
            nivel='junior', observacoes=(
                "Artefatos:\n"
                "  - roteiro-demo.md: cenarios de apresentacao\n"
                "  - postman-collection.json + environment.json\n"
                "  - queries.sql: consultas antes/depois"
            ),
            tipo='demo',
            dependeDe=[task_list[4 if not precisa_calculo else 5]['id']],
            artefatos=['roteiro-demo.md', 'postman-collection.json',
                       'postman-environment.json', 'queries.sql']))

    elif granularity == 'fina':
        # --- Task 1: Migration ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar migration Liquibase de {domain}",
            nivel='junior', observacoes=(
                "Criar changeset Liquibase:\n"
                "  1. Criacao de sequence\n"
                "  2. Criacao de tabela com colunas, PK, FKs, indices\n"
                "  3. Inserts de dados iniciais (se aplicavel)\n\n"
                "Siga o padrao de migrations existentes no projeto\n"
                "Nome do arquivo: YYYYMMDDHHMM_descricao.xml"
            ),
            tipo='criar-classe', dependeDe=[]))

        # --- Task 2: Entity ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar entidade JPA de {domain}",
            nivel='junior', observacoes=(
                f"Criar classe no pacote .domain:\n"
                f"  - @Entity @Table @SequenceGenerator @Alias\n"
                f"  - Campos mapeados com @Id, @Column, @ManyToOne\n"
                f"  - Lombok: @Data @Builder @NoArgsConstructor @AllArgsConstructor"
            ),
            tipo='criar-classe', dependeDe=[task_list[0]['id']]))

        # --- Task 3: DTOs ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar DTOs (input/output/filter) de {domain}",
            nivel='junior', observacoes=(
                "Criar classes no pacote .model:\n"
                "  1. Input DTO: campos com @NotBlank @NotNull @Max\n"
                "  2. Output DTO: campos de exibicao\n"
                "  3. Filter DTO: parametros de consulta\n\n"
                "Lombok: @Data @Builder @NoArgsConstructor @AllArgsConstructor"
            ),
            tipo='criar-classe', dependeDe=[task_list[1]['id']]))

        # --- Task 4: Repository ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar repository de {domain}",
            nivel='junior', observacoes=(
                "Criar interface no pacote .repository:\n"
                "  - extends JpaRepository<Entity, Long>\n"
                "  - Metodos de busca customizados (@Query se necessario)\n"
                "  - Paginacao e ordenacao"
            ),
            tipo='criar-classe', dependeDe=[task_list[2]['id']]))

        # --- Task 5: Mapper ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar mapper (MapStruct) de {domain}",
            nivel='junior', observacoes=(
                "Criar interface no pacote .converter:\n"
                "  - @Mapper(componentModel = \"spring\")\n"
                "  - Metodos: toEntity, toOutput, toFilter\n"
                "  - Mapping de entidades relacionadas"
            ),
            tipo='criar-classe', dependeDe=[task_list[3]['id']]))

        # --- Task 6: Service ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Implementar service + actions de {domain}",
            nivel='pleno', observacoes=(
                "Criar classes no pacote .service:\n"
                "  - Service com @Service @Slf4j @Transactional\n"
                "  - Actions (validator, get, save, delete) se houver padrao\n"
                "  - Regras de negocio e validacoes\n"
                "  - Tratamento de excecoes"
            ),
            tipo='implementar', dependeDe=[task_list[4]['id']]))

        # --- Task 7: Controller ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar controller REST de {domain}",
            nivel='pleno', observacoes=(
                "Criar classe no pacote .controller:\n"
                "  - @RestController @RequestMapping @RequiredArgsConstructor\n"
                "  - Endpoints: GET (listar), POST (criar), PUT (alterar), DELETE (excluir)\n"
                "  - ResponseEntity com tratamento de erros"
            ),
            tipo='adicionar-endpoint', dependeDe=[task_list[5]['id']]))

        # --- Task 8: Testes unitarios ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Testes unitarios de {domain}",
            nivel='junior', observacoes=(
                "Testes com JUnit + Mockito:\n"
                "  - Service: cenarios de sucesso e erro\n"
                "  - Controller: MockMvc\n"
                "  - Repository: @DataJpaTest com H2"
            ),
            tipo='testes', dependeDe=[task_list[6]['id']]))

        # --- Task 9: Testes integracao ---
        task_list.append(dict(**K, id=nid(),
            descricao=f"Testes de integracao de {domain}",
            nivel='pleno', observacoes=(
                "Testes de fluxo completo:\n"
                "  - HTTP → controller → service → repository → banco\n"
                "  - Cenarios de contorno (erro, validacao, conflito)\n"
                "  - Cobertura minima: 80%"
            ),
            tipo='testes', dependeDe=[task_list[7]['id']]))

        # --- Task 10: Logica (condicional) ---
        if precisa_calculo:
            task_list.append(dict(**K, id=nid(),
                descricao=f"Implementar logica de processamento/calculo de {domain}",
                nivel='senior', observacoes=(
                    "Implementar no service existente:\n"
                    "  - Algoritmo de calculo conforme requisitos\n"
                    "  - Arredondamento e precisao numerica\n\n"
                    "Testes:\n"
                    "  - Unitarios: cenario de calculo com valores conhecidos\n"
                    "  - Comparacao com resultados esperados\n\n"
                    "[Senior] Task de maior risco tecnico"
                ),
                tipo='alterar-classe',
                dependeDe=[task_list[8]['id']]))

        # --- Task 11: Demo ---
        dep_idx = 8 if not precisa_calculo else 9
        task_list.append(dict(**K, id=nid(),
            descricao=f"Preparar artefatos de demonstracao de {domain}",
            nivel='junior', observacoes=(
                "Artefatos:\n"
                "  - roteiro-demo.md: cenarios de apresentacao\n"
                "  - postman-collection.json + environment.json\n"
                "  - queries.sql: consultas antes/depois"
            ),
            tipo='demo',
            dependeDe=[task_list[dep_idx]['id']],
            artefatos=['roteiro-demo.md', 'postman-collection.json',
                       'postman-environment.json', 'queries.sql']))

    tasks.extend(task_list)
    return tasks


def javascript_tasks(config, scan_data, jira_data, keywords, ticket_id, granularity='grossa'):
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

    task_list = []

    if granularity == 'grossa':
        task_list.append(dict(**K, id=nid(),
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

    elif granularity == 'media':
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar servico de API de {domain}",
            nivel='junior', observacoes=(
                "Criar servico de comunicacao com API:\n"
                "  1. Metodos CRUD (fetch/axios)\n"
                "  2. Tratamento de erros e loading\n"
                "  3. Tipos/Interfaces TypeScript"
            ),
            tipo='criar-classe', dependeDe=[]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar componentes de UI de {domain}",
            nivel='pleno', observacoes=(
                "Criar componentes React:\n"
                "  1. Componente de listagem com tabela\n"
                "  2. Modal/pagina de criacao/edicao\n"
                "  3. Formularios com validacao\n"
                "  4. Integracao com servico de API"
            ),
            tipo='implementar', dependeDe=[task_list[0]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Testes de {domain}",
            nivel='junior', observacoes=(
                "Testes:\n"
                "  - Unitarios: componentes com Jest/Vitest\n"
                "  - Integracao: Cypress/Playwright se houver\n"
                "  - Cobertura: 80% linhas novas"
            ),
            tipo='testes', dependeDe=[task_list[1]['id']]))

    elif granularity == 'fina':
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar tipos/interfaces de {domain}",
            nivel='junior', observacoes=(
                "Criar tipos TypeScript no modelo de dados do dominio"
            ),
            tipo='criar-classe', dependeDe=[]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar servico de API de {domain}",
            nivel='junior', observacoes=(
                "Servico com metodos CRUD + tratamento de erros"
            ),
            tipo='criar-classe', dependeDe=[task_list[0]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar hook + estado de {domain}",
            nivel='pleno', observacoes=(
                "Hooks customizados com estado, loading e cache"
            ),
            tipo='criar-classe', dependeDe=[task_list[1]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar componente de listagem de {domain}",
            nivel='junior', observacoes=(
                "Componente de tabela/listagem com filtros e paginacao"
            ),
            tipo='criar-classe', dependeDe=[task_list[2]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar formulario de {domain}",
            nivel='pleno', observacoes=(
                "Formulario de criacao/edicao com validacao"
            ),
            tipo='criar-classe', dependeDe=[task_list[3]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Testes de {domain}",
            nivel='junior', observacoes="Testes unitarios e integracao",
            tipo='testes', dependeDe=[task_list[4]['id']]))

    # Demo task (sempre presente)
    task_list.append(dict(**K, id=nid(),
        descricao=f"Preparar demonstracao de {domain}",
        nivel='junior',
        observacoes="Roteiro de demonstracao funcional da interface implementada",
        tipo='demo',
        dependeDe=[task_list[0]['id'] if granularity == 'grossa' else task_list[-2]['id']],
        artefatos=['roteiro-demo.md']))

    tasks.extend(task_list)
    return tasks


def generic_tasks(config, scan_data, jira_data, keywords, ticket_id, granularity='grossa'):
    """Gera tasks verticais consolidadas para linguagens nao mapeadas."""
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

    task_list = []

    if granularity == 'grossa':
        task_list.append(dict(**K, id=nid(),
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

    elif granularity == 'media':
        task_list.append(dict(**K, id=nid(),
            descricao=f"Implementar logica principal de {domain}",
            nivel='pleno', observacoes=(
                "Implementar a logica de negocio principal com testes unitarios"
            ),
            tipo='implementar', dependeDe=[]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar interface/API de {domain}",
            nivel='junior', observacoes=(
                "Criar endpoints de entrada/saida da funcionalidade"
            ),
            tipo='adicionar-endpoint', dependeDe=[task_list[0]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Testes de integracao de {domain}",
            nivel='junior', observacoes="Testes de fluxo completo",
            tipo='testes', dependeDe=[task_list[1]['id']]))

    elif granularity == 'fina':
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar modelo de dados de {domain}",
            nivel='junior', observacoes="Definir estrutura de dados da funcionalidade",
            tipo='criar-classe', dependeDe=[]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Implementar regras de negocio de {domain}",
            nivel='pleno', observacoes="Logica principal com validacoes",
            tipo='implementar', dependeDe=[task_list[0]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Criar interface de entrada de {domain}",
            nivel='junior', observacoes="CLI/API/endpoint da funcionalidade",
            tipo='adicionar-endpoint', dependeDe=[task_list[1]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Testes unitarios de {domain}",
            nivel='junior', observacoes="Testes unitarios da logica e interface",
            tipo='testes', dependeDe=[task_list[2]['id']]))
        task_list.append(dict(**K, id=nid(),
            descricao=f"Testes de integracao de {domain}",
            nivel='pleno', observacoes="Testes de fluxo completo",
            tipo='testes', dependeDe=[task_list[3]['id']]))

    # Demo
    dep_idx = 0 if granularity == 'grossa' else (len(task_list) - 1)
    task_list.append(dict(**K, id=nid(),
        descricao=f"Preparar demonstracao de {domain}",
        nivel='junior',
        observacoes="Roteiro de demonstracao",
        tipo='demo', dependeDe=[task_list[dep_idx]['id']],
        artefatos=['roteiro-demo.md']))

    tasks.extend(task_list)
    return tasks


# ---------------------------------------------------------------------------
# Geracao de tasks a partir de subtasks reais do Jira
# ---------------------------------------------------------------------------


def from_jira_tasks(config, scan_data, jira_data, ticket_id):
    """Gera tasks a partir das subtasks reais do Jira (--from-jira mode).

    Cada subtask vira uma task em status-tasks.json com:
      - jiraKey: identificador da subtask no Jira
      - tipo/nivel: auto-detectados pelo summary
      - dependeDe: ordem sequencial das subtasks
      - observacoes: enriquecidas com contexto do codigo fonte
    """
    tasks = []
    task_id = [0]

    def nid():
        task_id[0] += 1
        return f"{task_id[0]:04d}"

    K = dict(projeto=config['name'], caminhoProjeto=config['path'],
             bloqueadoPor=None, status='pendente')

    subtasks = jira_data.get('subtasks', [])
    if not subtasks:
        return tasks, 'no_subtasks'

    pkg = detect_base_package(scan_data)
    project_conventions = extract_project_conventions(scan_data)

    def extract_adf_text(adf_value):
        """Extrai texto de um campo ADF (Atlassian Document Format)."""
        if not adf_value:
            return ''
        if isinstance(adf_value, str):
            return adf_value
        texts = []

        def _extract(node):
            if isinstance(node, dict):
                if node.get('type') == 'text' and node.get('text'):
                    texts.append(node['text'])
                for v in node.values():
                    _extract(v)
            elif isinstance(node, list):
                for item in node:
                    _extract(item)

        _extract(adf_value)
        return '\n'.join(texts)

    def strip_html(html_text):
        if not html_text:
            return ''
        import re
        return re.sub(r'<[^>]+>', ' ', html_text).strip()

    all_prev_ids = []
    for sub in subtasks:
        summary = sub.get('summary', '')
        sub_key = sub.get('key', '')

        # Extrair descricao (rendered HTML > ADF > vazio)
        desc_html = sub.get('descriptionRendered', '') or ''
        desc_adf = sub.get('description', '') or ''
        desc_text = strip_html(desc_html) if desc_html else extract_adf_text(desc_adf)

        # --- Auto-detectar tipo ---
        sl = summary.lower()
        if any(w in sl for w in ['crud', 'criar', 'nov', 'cadastr', 'incluir']):
            tipo = 'implementar'
            nivel = 'junior'
        elif any(w in sl for w in ['calcul', 'processamento', 'logica', 'processar']):
            tipo = 'alterar-classe'
            nivel = 'senior'
        elif any(w in sl for w in ['ajust', 'alter', 'modific', 'adapt']):
            tipo = 'alterar-classe'
            nivel = 'pleno'
        elif any(w in sl for w in ['test', 'validar']):
            tipo = 'testes'
            nivel = 'junior'
        elif any(w in sl for w in ['demo', 'apresent', 'artefato']):
            tipo = 'demo'
            nivel = 'junior'
        else:
            tipo = 'implementar'
            nivel = 'pleno'

        # --- Auto-detectar dependencia: ultima task do mesmo tipo ou sequencial ---
        dependeDe = []
        if all_prev_ids:
            dependeDe = [all_prev_ids[-1]]

        # --- Montar observacoes enriquecidas ---
        obs_lines = []
        if sub_key:
            obs_lines.append(f"Subtask Jira: {sub_key}")
        obs_lines.append(f"Descricao: {summary}")
        if desc_text:
            obs_lines.append(f"")
            for line in desc_text.strip().split('\n'):
                line = line.strip()
                if line:
                    obs_lines.append(f"  {line}")
        if pkg:
            obs_lines.append(f"")
            obs_lines.append(f"Pacote base: {pkg}")

        if tipo == 'implementar':
            obs_lines.extend([
                f"",
                f"Arquivos a criar:",
                f"  1. Migration Liquibase (se nova entidade/tabela)",
                f"  2. Entidade JPA no pacote .domain",
                f"  3. DTOs de input/output no pacote .model",
                f"  4. Repository (Spring Data JPA) no pacote .repository",
                f"  5. Service com regras de negocio no pacote .service",
                f"  6. Controller REST no pacote .controller",
                f"  7. Testes unitarios + integracao",
                f"",
                f"Convencoes: @Entity, @Data, @RequiredArgsConstructor, @RestController",
            ])
        elif tipo == 'alterar-classe':
            obs_lines.extend([
                f"",
                f"Acoes:",
                f"  1. Localizar classes existentes a modificar no pacote {pkg}",
                f"  2. Adicionar/alterar logica mantendo compatibilidade",
                f"  3. Atualizar validators e actions se necessario",
                f"  4. Adicionar testes de regressao",
                f"",
                f"Atencao: nao quebrar fluxos existentes",
            ])
        elif tipo == 'demo':
            obs_lines.extend([
                f"",
                f"Artefatos:",
                f"  - roteiro-demo.md: cenarios de apresentacao",
                f"  - postman-collection.json: requests por cenario",
                f"  - postman-environment.json: variaveis",
                f"  - queries.sql: consultas antes/depois",
            ])

        if project_conventions:
            obs_lines.append(f"\n--- Contexto do Projeto ---\n{project_conventions}")

        observacoes = '\n'.join(obs_lines)

        prev_id = nid()
        task = dict(**K, id=prev_id, jiraKey=sub_key,
                    descricao=summary, nivel=nivel, observacoes=observacoes,
                    tipo=tipo, dependeDe=dependeDe)
        tasks.append(task)
        all_prev_ids.append(prev_id)

    return tasks, 'from_jira'


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
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("Uso: generate-tasks.py TICKET_DIR [CONFIG_FILE] [--granularity grossa|media|fina] [--from-jira] [--preview]", file=sys.stderr)
        sys.exit(1)

    ticket_dir = sys.argv[1]

    # Parse args
    preview_only = False
    granularity = 'grossa'
    from_jira = False
    config_file_env = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--preview':
            preview_only = True
            i += 1
        elif args[i] == '--from-jira':
            from_jira = True
            i += 1
        elif args[i] == '--granularity' and i + 1 < len(args):
            granularity = args[i + 1]
            i += 2
        elif args[i].startswith('--granularity='):
            granularity = args[i].split('=', 1)[1]
            i += 1
        elif not args[i].startswith('--'):
            config_file_env = args[i]
            i += 1
        else:
            i += 1

    config_file = config_file_env or find_config(ticket_dir)

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

    # --- SUGERIR GRANULARIDADE SE NAO FOI ESPECIFICADA ---
    explicit_granularity = any('--granularity' in a for a in sys.argv[1:])
    if not explicit_granularity:
            scan_data_global = load_json(os.path.join(ticket_dir, 'impact-report.json'))
            suggested, motivo = suggest_granularity(keywords, jira_data, scan_data_global)
            granularity = suggested
            print(f"[TASKS] Granularidade auto-detectarada: {suggested}", file=sys.stderr)
            print(f"[TASKS] Motivo: {motivo}", file=sys.stderr)

    # Carregar contextos dos projetos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_contexts = {}
    candidate_dirs = [
        os.path.join(script_dir, '..', 'projects-context'),
        os.path.join(script_dir, 'projects-context'),
        os.path.join(script_dir, '..', '..', 'projects-context'),
    ]
    context_dir = None
    for d in candidate_dirs:
        d = os.path.abspath(d)
        if os.path.isdir(d):
            context_dir = d
            break

    all_tasks = []
    ticket_projects = []

    for proj in projects:
        proj_name = proj.get('name', 'projeto')
        # Carregar contexto do projeto
        if context_dir:
            ctx_file = os.path.join(context_dir, f'{proj_name}.md')
            if os.path.isfile(ctx_file):
                proj_ctx = load_project_context(proj_name, script_dir)
                if proj_ctx:
                    project_contexts[proj_name] = proj_ctx
                    controllers = ', '.join(proj_ctx.get('controllers', [])[:3])
                    services = ', '.join(proj_ctx.get('services', [])[:3])
                    if controllers or services:
                        print(f"[TASKS] Contexto carregado para {proj_name}: {controllers} | {services}", file=sys.stderr)
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

        if from_jira:
            proj_tasks, mode = from_jira_tasks(proj, scan_data, jira_data, ticket_id)
            if mode == 'no_subtasks':
                print(f"[TASKS] AVISO: Nenhuma subtask encontrada no Jira para {proj_name}. Gerando por granularidade ({granularity}) como fallback.", file=sys.stderr)
                handler = LANGUAGE_HANDLERS.get(lang, generic_tasks)
                proj_tasks = handler(proj, scan_data, jira_data, keywords, ticket_id, granularity)
        else:
            handler = LANGUAGE_HANDLERS.get(lang, generic_tasks)
            proj_tasks = handler(proj, scan_data, jira_data, keywords, ticket_id, granularity)

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

    # --- ENRIQUECER OBSERVACOES COM CONTEXTO DO PROJETO ---
    for t in all_tasks:
        proj_name = t.get('projeto', '')
        proj_ctx = project_contexts.get(proj_name)
        if proj_ctx and 'observacoes' in t:
            t['observacoes'] = enrich_observations(
                t['observacoes'], proj_ctx,
                task_type=t.get('tipo'),
                domain_name=t.get('descricao', '')
            )

    # --- ADICIONAR ESTIMATIVA DE ESFORCO ---
    for t in all_tasks:
        estimativa = estimate_effort(t.get('tipo', 'implementar'), t.get('nivel', 'pleno'))
        t['esforcoEstimado'] = estimativa

    if not all_tasks:
        print("[TASKS] Nenhuma task gerada", file=sys.stderr)
        sys.exit(0)

    if preview_only:
        granularity_label = {'grossa': '3 tasks', 'media': '6-7 tasks', 'fina': '10-11 tasks'}.get(granularity, granularity)
        print(f"[PREVIEW] Granularidade: {granularity} ({granularity_label})", file=sys.stderr)
        print(f"{'ID':>6} | {'Descricao':<55} | {'Nivel':<8} | {'Tipo':<15} | {'Esforco':<10} | {'Depende':<12}")
        print('-' * 115)
        for t in all_tasks:
            deps = ', '.join(t.get('dependeDe', [])) or '-'
            desc = t.get('descricao', '')[:55]
            esforco = t.get('esforcoEstimado', {}).get('descricao', '?')
            print(f"{t['id']:>6} | {desc:<55} | {t.get('nivel',''):<8} | {t.get('tipo',''):<15} | {esforco:<10} | {deps:<12}")
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
