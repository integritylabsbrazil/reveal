#!/usr/bin/env python3
"""Gera openapi.yaml para um ticket a partir dos dados do refinamento.

Uso: python3 generate_openapi_spec.py TICKET_DIR

Le:
  - jira-data.json       (ticket metadata, campos customizados)
  - status-tasks.json    (tasks com observacoes que contem endpoints/DTOs)
  - refinamento-tecnico.md (opcional, para contexto adicional)
  - projects-context/*.md (convencoes do projeto)
  - refine-config.json   (apiBaseUrl do projeto)
  - codigo fonte do projeto (DTOs reais, se disponivel)

Gera:
  - tickets/TICKET_ID/openapi.yaml
"""

import json
import os
import re
import sys
from datetime import datetime
from collections import defaultdict


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def detect_projects(ticket_dir):
    """Detecta quais projetos estao envolvidos no ticket."""
    tasks_file = os.path.join(ticket_dir, 'status-tasks.json')
    tasks = load_json(tasks_file)
    projetos = tasks.get('projetosEnvolvidos', [])
    if not projetos:
        for t in tasks.get('tarefas', []):
            p = t.get('projeto', '').strip()
            if p and p not in projetos:
                projetos.append(p)
    return projetos


def load_project_config(script_dir, project_name):
    """Carrega configuracao do projeto (apiBaseUrl, etc.)."""
    config_paths = [
        os.path.join(script_dir, 'refine-config.local.json'),
        os.path.join(script_dir, 'refine-config.json'),
    ]
    for cp in config_paths:
        config = load_json(cp)
        for p in config.get('projects', []):
            if p.get('name') == project_name:
                return p
    return {}


def load_project_context(script_dir, project_name):
    """Carrega projects-context/<projeto>.md para extrair tags, base path."""
    ctx_file = os.path.join(script_dir, 'projects-context', f'{project_name}.md')
    if not os.path.exists(ctx_file):
        return {}
    with open(ctx_file) as f:
        content = f.read()

    ctx = {}

    req_mappings = re.findall(r'@RequestMapping\(["\']?([^"\'()]+)["\']?\)', content)
    if req_mappings:
        ctx['base_paths'] = list(set(req_mappings))

    tags = re.findall(r'@Tag\(name\s*=\s*"([^"]+)"(?:,\s*description\s*=\s*"([^"]*)")?\)', content)
    if tags:
        ctx['api_tags'] = [{'name': n, 'description': d or n} for n, d in tags]

    operations = re.findall(r'@Operation\(description\s*=\s*"([^"]+)"\)', content)
    if operations:
        ctx['operations'] = operations

    return ctx


def extract_endpoints_from_obs(obs_text):
    """Extrai endpoints de observacoes markdown com code blocks."""
    endpoints = []
    if not obs_text:
        return endpoints

    method_patterns = [
        (r'@GetMapping\s*\(\s*"?([^"()]+)"?\s*\)', 'get'),
        (r'@PostMapping\s*\(\s*"?([^"()]+)"?\s*\)', 'post'),
        (r'@PutMapping\s*\(\s*"?([^"()]+)"?\s*\)', 'put'),
        (r'@DeleteMapping\s*\(\s*"?([^"()]+)"?\s*\)', 'delete'),
        (r'@PatchMapping\s*\(\s*"?([^"()]+)"?\s*\)', 'patch'),
    ]

    for pattern, method in method_patterns:
        for match in re.finditer(pattern, obs_text):
            path = match.group(1).strip()
            summary = ''
            op_match = re.search(r'@Operation\(description\s*=\s*"([^"]+)"\)', obs_text[max(0, match.start()-500):match.end()+200])
            if op_match:
                summary = op_match.group(1)
            if not summary:
                summary = path.replace('/', ' ').strip().capitalize()

            endpoints.append({
                'method': method,
                'path': path,
                'summary': summary,
                'operationId': f'{method}{path.replace("/", "_").replace("{", "").replace("}", "")}'.lower(),
                'tags': [],
                'parameters': [],
                'requestBody': None,
                'responses': {},
            })

    list_patterns = [
        (r'`(GET)\s+([^\s`]+)`[^`]*?[-–—]\s*(.*?)$', 'get'),
        (r'`(POST)\s+([^\s`]+)`[^`]*?[-–—]\s*(.*?)$', 'post'),
        (r'`(PUT)\s+([^\s`]+)`[^`]*?[-–—]\s*(.*?)$', 'put'),
        (r'`(DELETE)\s+([^\s`]+)`[^`]*?[-–—]\s*(.*?)$', 'delete'),
        (r'`(PATCH)\s+([^\s`]+)`[^`]*?[-–—]\s*(.*?)$', 'patch'),
        (r'`(GET)\s+([^\s`]+)`', 'get'),
        (r'`(POST)\s+([^\s`]+)`', 'post'),
        (r'`(PUT)\s+([^\s`]+)`', 'put'),
        (r'`(DELETE)\s+([^\s`]+)`', 'delete'),
        (r'`(PATCH)\s+([^\s`]+)`', 'patch'),
    ]

    for pattern, method in list_patterns:
        for match in re.finditer(pattern, obs_text, re.MULTILINE):
            method_str = match.group(1).lower()
            path = match.group(2).strip()
            if not path.startswith('/'):
                path = '/' + path
            summary = match.group(3).strip() if match.lastindex >= 3 else ''
            if not summary:
                summary = path.replace('/', ' ').strip().capitalize()

            key = (method_str, path)
            if key not in [(e['method'], e['path']) for e in endpoints]:
                endpoints.append({
                    'method': method_str,
                    'path': path,
                    'summary': summary,
                    'operationId': f'{method_str}{path.replace("/", "_").replace("{", "").replace("}", "")}'.lower(),
                    'tags': [],
                    'parameters': [],
                    'requestBody': None,
                    'responses': {},
                })

    return endpoints


def extract_dtos_from_obs(obs_text):
    """Extrai DTOs de code blocks Java em observacoes e de tabelas markdown."""
    schemas = {}
    if not obs_text:
        return schemas

    code_blocks = re.findall(r'```java\n(.*?)```', obs_text, re.DOTALL)
    for block in code_blocks:
        class_matches = re.finditer(
            r'(?:public\s+)?(?:class|record)\s+(\w+)(?:\s+implements\s+\w+)?(?:\s*\{)',
            block
        )
        for cm in class_matches:
            class_name = cm.group(1)
            if not re.search(r'(Input|Output|DTO|Filter|Request|Response|Dto|dto)$', class_name):
                continue
            fields = []
            for field_match in re.finditer(
                r'(?:private\s+)?(\w+(?:<\w+>)?)\s+(\w+)\s*(?:;|=)',
                block[cm.end():cm.end()+500]
            ):
                ftype = field_match.group(1)
                fname = field_match.group(2)
                mapped_type = java_to_openapi_type(ftype)
                fields.append({
                    'name': fname,
                    'type': mapped_type,
                    'description': _field_name_to_description(fname),
                    'required': True if re.search(r'@NotBlank|@NotNull|@NotEmpty', block[max(0, field_match.start()-200):field_match.start()]) else False,
                })
            schemas[class_name] = {
                'type': 'object',
                'fields': fields,
            }

    # Tambem extrair de tabelas markdown: | NomeClasse.java | ACAO | pacote |
    # Captura classes DTO/Filter mencionadas mesmo sem code block
    table_matches = re.finditer(
        r'\| (\w+(?:Input|Output|DTO|Filter|Request|Response|Dto)\.java) \|.*?(?:NOVA|ALTERAR|CRIAR)',
        obs_text
    )
    for tm in table_matches:
        class_name = tm.group(1).replace('.java', '')
        if class_name not in schemas:
            # Tentar buscar fields do DTO Input/Output correspondente
            base = re.sub(r'(Input|Output|DTO|Filter|Request|Response|Dto)$', '', class_name)
            # Clonar fields do schema que contem a base, se existir
            fields = []
            for existing_name, existing_data in schemas.items():
                if base and existing_name.startswith(base) and existing_name != class_name:
                    fields = existing_data.get('fields', [])
                    break
            schemas[class_name] = {
                'type': 'object',
                'fields': fields,
            }

    return schemas


def java_to_openapi_type(java_type):
    """Mapeia tipo Java para OpenAPI type."""
    mapping = {
        'String': 'string',
        'Long': 'integer',
        'long': 'integer',
        'Integer': 'integer',
        'int': 'integer',
        'Double': 'number',
        'double': 'number',
        'BigDecimal': 'number',
        'Float': 'number',
        'float': 'number',
        'Boolean': 'boolean',
        'boolean': 'boolean',
        'LocalDate': 'string',
        'LocalDateTime': 'string',
        'Date': 'string',
        'List': 'array',
        'Set': 'array',
        'UUID': 'string',
    }
    base = java_type.split('<')[0]
    return mapping.get(base, 'string')


def _field_name_to_description(name):
    """Converte nome de campo camelCase para descricao legivel."""
    if not name:
        return ''
    # Separar em palavras: quantidadeCasasDecimais -> quantidade, Casas, Decimais
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$|\d)|\d+', name)
    if not words:
        return name
    desc = ' '.join(w.lower() for w in words)
    return desc.capitalize()


def _type_to_example(oa_type):
    """Gera valor exemplo para um tipo OpenAPI."""
    examples = {
        'string': 'exemplo',
        'integer': 0,
        'number': 0.0,
        'boolean': True,
        'array': [],
        'object': {},
    }
    return examples.get(oa_type, 'exemplo')


def _generate_schema_example(fields):
    """Gera exemplo a partir de lista de campos."""
    if not fields:
        return {}
    example = {}
    for f in fields:
        example[f['name']] = _type_to_example(f['type'])
    return example


def _path_to_entity_name(path):
    """Extrai nome de entidade de um path. Ex: /parametros-cota -> ParametroCotaPatrimonial."""
    parts = [p for p in path.split('/') if p and not p.startswith('{')]
    if not parts:
        return ''
    # Pegar a ultima parte significativa
    entity_part = parts[-1]
    # Converter kebab para camel e capitalizar
    words = entity_part.split('-')
    camel = ''.join(w.capitalize() for w in words)
    # Singularizar se terminar em 's'
    if camel.endswith('s') and len(camel) > 4:
        camel = camel[:-1]
    return camel


def _build_endpoint_description(ep, task_context):
    """Gera descricao expandida para um endpoint.

    Usa o summary + contexto da task + nome da entidade.
    """
    method = ep['method'].upper()
    path = ep['path']
    summary = ep['summary'] or ''
    entity = _path_to_entity_name(path)

    # Verbos por metodo
    verb_map = {
        'get': 'Retorna',
        'post': 'Cria',
        'put': 'Atualiza',
        'delete': 'Remove',
        'patch': 'Atualiza parcialmente',
    }
    verb = verb_map.get(ep['method'], 'Processa')

    has_id = '{id}' in path
    is_list = ep['method'] == 'get' and not has_id

    if summary and len(summary) > 10:
        desc = summary
        if not desc.endswith('.'):
            desc += '.'
        return desc

    if is_list:
        desc = f'{verb} lista de {entity.lower()} com suporte a paginacao e filtros.'
    elif has_id and ep['method'] == 'get':
        desc = f'{verb} um {entity.lower()} especifico pelo ID.'
    elif has_id and ep['method'] == 'delete':
        desc = f'{verb} um {entity.lower()} especifico pelo ID.'
    elif has_id:
        desc = f'{verb} um {entity.lower()} especifico pelo ID.'
    else:
        desc = f'{verb} um {entity.lower()}.'

    return desc


def extract_description_sections(desc_text):
    """Extrai secoes da descricao enriquecida (description.md)."""
    endpoints = []
    schemas = {}

    if not desc_text:
        return endpoints, schemas

    table_pattern = re.findall(
        r'\|.*?(GET|POST|PUT|DELETE|PATCH).*?\|.*?/([^|]+).*?\|.*?([^|]*?)\|',
        desc_text, re.IGNORECASE
    )
    for method, path, desc in table_pattern:
        endpoints.append({
            'method': method.lower(),
            'path': '/' + path.strip(),
            'summary': desc.strip() or path.strip(),
            'operationId': f'{method.lower()}_{path.strip().replace("/", "_").replace("{", "").replace("}", "")}',
            'tags': [],
            'parameters': [],
            'requestBody': None,
            'responses': {},
        })

    schema_tables = re.finditer(
        r'### ([A-Za-z]+(?:Input|Output|DTO|Filter|Request|Response))\s*\n\|.*?\n\|.*?\n((?:\|.*?\n)*)',
        desc_text, re.MULTILINE
    )
    for st in schema_tables:
        name = st.group(1)
        rows = re.findall(r'\|(\w+)\s*\|(\w+(?:<.*?>)?)\s*\|([^|]*?)\|', st.group(2))
        fields = []
        for fname, ftype, fmeta in rows:
            required = 'sim' in fmeta.lower() or 'true' in fmeta.lower()
            fields.append({
                'name': fname.strip(),
                'type': java_to_openapi_type(ftype.strip()),
                'description': fmeta.strip() or _field_name_to_description(fname.strip()),
                'required': required,
            })
        if name not in schemas:
            schemas[name] = {'type': 'object', 'fields': fields}

    json_blocks = re.findall(r'```json\n(.*?)```', desc_text, re.DOTALL)
    for jb in json_blocks:
        try:
            data = json.loads(jb)
            if isinstance(data, list) and data:
                data = data[0]
            if isinstance(data, dict):
                schema_name = 'GeneratedSchema'
                fields = []
                for key, val in data.items():
                    val_type = type(val).__name__
                    if val_type == 'str':
                        oa_type = 'string'
                    elif val_type in ('int', 'float'):
                        oa_type = 'number'
                    elif val_type == 'bool':
                        oa_type = 'boolean'
                    elif val_type == 'list':
                        oa_type = 'array'
                    elif val_type == 'dict':
                        oa_type = 'object'
                    else:
                        oa_type = 'string'
                    fields.append({
                        'name': key,
                        'type': oa_type,
                        'description': _field_name_to_description(key),
                        'required': True,
                    })
                header_match = re.search(r'# ([A-Za-z]+(?:Input|Output|DTO|Filter|Request|Response))', desc_text[:desc_text.find(jb)])
                if header_match:
                    schema_name = header_match.group(1)
                schemas[schema_name] = {'type': 'object', 'fields': fields}
        except json.JSONDecodeError:
            pass

    return endpoints, schemas


def scan_source_dtos(project_path, base_package):
    """Escaneia codigo fonte do projeto para extrair DTOs reais."""
    schemas = {}
    if not project_path or not os.path.isdir(project_path):
        return schemas

    src_dir = os.path.join(project_path, 'src', 'main', 'java')

    if not os.path.isdir(src_dir):
        src_dir = os.path.join(project_path, 'src')
    if not os.path.isdir(src_dir):
        return schemas

    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            if not fname.endswith('.java'):
                continue
            if not re.search(r'(Input|Output|DTO|Filter|Request|Response|Dto)\.java$', fname):
                continue

            fpath = os.path.join(root, fname)
            try:
                with open(fpath) as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            class_name = fname.replace('.java', '')

            fields = []
            for fm in re.finditer(
                r'(?:private\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*;',
                content
            ):
                ftype = fm.group(1)
                fname_field = fm.group(2)
                if fname_field.upper() == fname_field and len(fname_field) > 1:
                    continue
                pos = fm.start()
                before = content[max(0, pos-300):pos]
                required = bool(re.search(r'@NotBlank|@NotNull|@NotEmpty', before))

                fields.append({
                    'name': fname_field,
                    'type': java_to_openapi_type(ftype),
                    'description': _field_name_to_description(fname_field),
                    'required': required,
                })

            schemas[class_name] = {'type': 'object', 'fields': fields}

    return schemas


def extract_endpoints_from_tasks(tasks, project_context):
    """Extrai endpoints consolidados de todas as tasks."""
    all_endpoints = []
    seen = set()

    for task in tasks:
        desc = task.get('descricao', '')
        obs = task.get('observacoes', '')

        for ep in extract_endpoints_from_obs(obs):
            key = (ep['method'], ep['path'])
            if key not in seen:
                seen.add(key)
                all_endpoints.append(ep)

        if task.get('tipo') == 'adicionar-endpoint':
            path_match = re.search(r'(?:endpoint|criar|adicionar)\s+(?:o\s+)?(?:endpoint\s+)?(GET|POST|PUT|DELETE|PATCH)?\s*[`"]?/([a-z0-9_-]+(?:/\{[^}]+\})?[a-z0-9/_-]*)', desc, re.IGNORECASE)
            if path_match:
                method = (path_match.group(1) or 'GET').lower()
                path = '/' + path_match.group(2)
                key = (method, path)
                if key not in seen:
                    seen.add(key)
                    all_endpoints.append({
                        'method': method,
                        'path': path,
                        'summary': desc[:80],
                        'operationId': f'{method}_{path.replace("/", "_").replace("{", "").replace("}", "")}'.lower(),
                        'tags': [],
                        'parameters': [],
                        'requestBody': None,
                        'responses': {},
                    })

    return all_endpoints


def _extract_adf_text(node):
    """Extrai texto simples de um no ADF (Atlassian Document Format)."""
    if isinstance(node, dict):
        t = node.get('type', '')
        if t == 'text' and 'text' in node:
            return node['text']
        texts = []
        for child in node.get('content', []):
            texts.append(_extract_adf_text(child))
        return ''.join(texts)
    return ''


def detect_api_endpoints_needed(ticket_data, tasks):
    """Detecta se o ticket envolve endpoints de API."""
    text_to_check = ''

    desc_raw = ticket_data.get('basic', {}).get('description', '') or ''
    if isinstance(desc_raw, dict):
        desc = _extract_adf_text(desc_raw)
    elif isinstance(desc_raw, str):
        desc = desc_raw
    else:
        desc = ''
    text_to_check += desc + ' '

    summary = ticket_data.get('basic', {}).get('summary', '') or ''
    text_to_check += summary + ' '

    for t in tasks:
        text_to_check += t.get('descricao', '') + ' '
        text_to_check += t.get('observacoes', '') + ' '

    api_keywords = [
        r'endpoint', r'api', r'controller', r'rest', r'endpoint',
        r'@PostMapping', r'@GetMapping', r'@PutMapping', r'@DeleteMapping',
        r'endpoint [a-z]', r'criar endpoint', r'novo endpoint',
        r'consulta.*(?:por|via|pelo?)', r'busca.*(?:por|via)',
        r'GET', r'POST', r'PUT', r'DELETE',
        r'\/api\/', r'\/rest\/',
        r'RequestMapping', r'ResponseEntity',
    ]

    for kw in api_keywords:
        if re.search(kw, text_to_check, re.IGNORECASE):
            return True

    return False


def detect_task_api_involvement(tasks):
    """Detecta se as tasks envolvem alteracao de API."""
    for t in tasks:
        desc = t.get('descricao', '')
        obs = t.get('observacoes', '')
        texto = desc + ' ' + obs
        if re.search(r'@(Post|Get|Put|Delete|Patch)Mapping|@RequestMapping', texto):
            return True
        if re.search(r'RequestBody|ResponseEntity', texto):
            return True
    return False


def _kebab_to_camel(name):
    """Converte kebab-case para CamelCase (ex: parametros-cota -> ParametrosCota)."""
    return ''.join(word.capitalize() for word in name.replace('/', ' ').replace('{', '').replace('}', '').split('-'))


_JAVA_RESERVED = {
    'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
    'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
    'extends', 'false', 'final', 'finally', 'float', 'for', 'goto', 'if',
    'implements', 'import', 'instanceof', 'int', 'interface', 'long', 'native',
    'new', 'null', 'package', 'private', 'protected', 'public', 'return',
    'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this',
    'throw', 'throws', 'transient', 'true', 'try', 'void', 'volatile', 'while',
    'response', 'responsentity', 'restcontroller', 'requestbody',
    'requestmapping', 'getmapping', 'postmapping', 'putmapping',
    'deletemapping', 'patchmapping', 'pathvariable', 'requestparam',
    'requestheader', 'autowired', 'inject', 'resource', 'service',
    'repository', 'controller', 'component', 'configuration',
    'jparepository', 'crudrepository', 'jpabaserepository',
    'requiredargsconstructor', 'noargsconstructor', 'allargsconstructor',
    'data', 'getter', 'setter', 'tostring', 'equalsandhashcode',
    'builder', 'slf4j', 'log4j', 'logger',
    'findby', 'findallby', 'findpageby', 'searchby',
    'createfrom', 'create', 'update', 'delete', 'save',
    'findeventocontabilby',
}


def _is_domain_entity(name):
    """Filtra nomes que parecem entidades de dominio validas."""
    if not name or not name[0].isupper():
        return False
    if name.lower() in _JAVA_RESERVED:
        return False
    if len(name) < 6:
        return False
    vowels_lower = sum(1 for c in name if c.islower() and c in 'aeiou')
    if vowels_lower < 2 and len(name) > 8:
        caps = sum(1 for c in name if c.isupper())
        if caps < 2:
            return False
    lower = name.lower()
    if lower.endswith('mapper') or lower.endswith('validator'):
        return False
    return True


def _derive_entity_roots(endpoints, tasks, existing_schemas):
    """Deriva raizes de entidade (ex: 'ParametroCotaPatrimonial') do ticket."""
    candidates = set()

    for ep in endpoints:
        camel = _kebab_to_camel(ep['path'])
        candidates.add(camel)
        if camel.endswith('s') and len(camel) > 4:
            candidates.add(camel[:-1])

    for name in existing_schemas:
        candidates.add(name)
        base = re.sub(r'(Input|Output|DTO|Filter|Request|Response|Dto|Page|List)$', '', name)
        if base:
            candidates.add(base)

    for t in tasks:
        obs = t.get('observacoes', '')
        for m in re.finditer(r'\b(?:class|interface|record|@Service|@Repository|@RestController)\s+(\w+)', obs):
            candidates.add(m.group(1))
        for m in re.finditer(r'([A-Z][a-zA-Z]{5,}(?:Input|Output|DTO|Filter|Request|Response|Dto|Entity|Repository|Controller|Service))', obs):
            candidates.add(m.group(1))
            base = re.sub(r'(Input|Output|DTO|Filter|Request|Response|Dto|Entity|Repository|Controller|Service)$', '', m.group(1))
            if base and len(base) >= 6:
                candidates.add(base)

    for t in tasks:
        desc = t.get('descricao', '')
        for m in re.finditer(r'[A-Z][a-z]+[A-Z][a-zA-Z]{3,}', desc):
            candidates.add(m.group(0))

    entities = {c for c in candidates if _is_domain_entity(c)}
    return sorted(entities)


def _is_relevant_schema(schema_name, entity_roots):
    """Schema e relevante se contiver alguma raiz de entidade do ticket."""
    name_lower = schema_name.lower()
    for root in entity_roots:
        root_lower = root.lower()
        if root_lower in name_lower:
            return True
    return False


def _build_openapi_spec(ticket_id, summary, date, api_base_url, api_tags, paths_grouped, schemas_list, project_name):
    """Constroi o dict completo da especificacao OpenAPI 3.0."""
    spec = {
        'openapi': '3.0.3',
        'info': {
            'title': f'{ticket_id}: {summary}',
            'description': (
                f'Documentação gerada automaticamente pelo pipeline de refinamento.\n'
                f'Ticket: {ticket_id}\n'
                f'Projeto: {project_name}'
            ),
            'version': date,
        },
        'paths': {},
        'components': {
            'schemas': {},
        },
    }

    if api_base_url:
        spec['servers'] = [
            {'url': api_base_url, 'description': 'Ambiente de produção'}
        ]

    if api_tags:
        spec['tags'] = [{'name': t['name'], 'description': t['description']} for t in api_tags]

    # Paths -> percorrer paths_grouped
    for path_entry in sorted(paths_grouped, key=lambda x: x['path']):
        path = path_entry['path']
        spec['paths'][path] = {}
        for method_data in path_entry['methods']:
            method = method_data['method']
            method_upper = method.upper()
            # Add path to method_data for _build_endpoint_description
            method_data_with_path = dict(method_data, path=path)
            summary_text = method_data['summary'] or ''
            description_text = _build_endpoint_description(method_data_with_path, '')

            method_obj = {
                'operationId': method_data['operationId'],
                'summary': summary_text,
                'description': description_text,
                'tags': method_data['tags'],
                'parameters': [],
                'responses': {
                    '200': {
                        'description': 'Operação realizada com sucesso',
                    },
                },
            }

            # Path parameters from {id}
            path_params = re.findall(r'\{(\w+)\}', path)
            for pname in path_params:
                method_obj['parameters'].append({
                    'name': pname,
                    'in': 'path',
                    'required': True,
                    'description': _field_name_to_description(pname),
                    'schema': {
                        'type': 'integer',
                    },
                })

            # Query parameters from method_data parameters
            for p in method_data.get('parameters', []):
                method_obj['parameters'].append({
                    'name': p['name'],
                    'in': p.get('in', 'query'),
                    'required': p.get('required', False),
                    'description': p.get('description', ''),
                    'schema': {
                        'type': p.get('type', 'string'),
                    },
                })

            # Filter parameters for GET list endpoints
            is_list = '{id}' not in path
            if method_upper == 'GET' and is_list:
                filter_fields = _infer_filter_fields(schemas_list, path)
                if filter_fields:
                    description_text += _build_filter_example(filter_fields)
                    method_obj['description'] = description_text
                for f in filter_fields:
                    method_obj['parameters'].append({
                        'name': f['name'],
                        'in': 'query',
                        'required': False,
                        'description': f.get('description', _field_name_to_description(f['name'])),
                        'schema': {
                            'type': f['type'],
                        },
                    })

            # Request body for POST/PUT/PATCH
            method_upper = method.upper()
            if method_upper in ('POST', 'PUT', 'PATCH'):
                dto_name = _infer_request_dto(schemas_list, path)
                if dto_name:
                    method_obj['requestBody'] = {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': f'#/components/schemas/{dto_name}',
                                },
                                'example': _generate_schema_example(
                                    next((s['fields'] for s in schemas_list if s['name'] == dto_name), [])
                                ),
                            },
                        },
                    }

            # Response with DTO for GET (single/list)
            if method_upper in ('GET',):
                dto_name = _infer_response_dto(schemas_list, path)
                if dto_name:
                    content_example = _generate_schema_example(
                        next((s['fields'] for s in schemas_list if s['name'] == dto_name), [])
                    )
                    if is_list:
                        content_example = [content_example]
                    method_obj['responses']['200']['content'] = {
                        'application/json': {
                            'schema': {
                                'type': 'array' if is_list else 'object',
                                'items' if is_list else '$ref': (
                                    {'$ref': f'#/components/schemas/{dto_name}'} if is_list
                                    else f'#/components/schemas/{dto_name}'
                                ),
                            },
                            'example': content_example,
                        },
                    }

            spec['paths'][path][method] = method_obj

    # Schemas
    for s in schemas_list:
        spec['components']['schemas'][s['name']] = {
            'type': 'object',
            'properties': {},
        }
        for f in s['fields']:
            prop = {
                'type': f['type'],
                'description': f.get('description', ''),
            }
            spec['components']['schemas'][s['name']]['properties'][f['name']] = prop

            # Mark required fields
            if f.get('required'):
                if 'required' not in spec['components']['schemas'][s['name']]:
                    spec['components']['schemas'][s['name']]['required'] = []
                spec['components']['schemas'][s['name']]['required'].append(f['name'])

        # Add example for the schema
        spec['components']['schemas'][s['name']]['example'] = _generate_schema_example(s['fields'])

    return spec


def _infer_request_dto(schemas_list, path):
    """Tenta inferir qual DTO usar como request body."""
    entity = _path_to_entity_name(path)
    for s in schemas_list:
        if entity and s['name'].startswith(entity):
            if s['name'].endswith('Input') or s['name'].endswith('Request'):
                return s['name']
    for s in schemas_list:
        if s['name'].endswith('Input') or s['name'].endswith('Request'):
            return s['name']
    return None


def _infer_response_dto(schemas_list, path):
    """Tenta inferir qual DTO usar como resposta."""
    entity = _path_to_entity_name(path)
    for s in schemas_list:
        if entity and s['name'].startswith(entity):
            if s['name'].endswith('Output') or s['name'].endswith('Response'):
                return s['name']
    for s in schemas_list:
        if s['name'].endswith('Output') or s['name'].endswith('Response'):
            return s['name']
    return None


def _infer_filter_dto(schemas_list, path):
    """Tenta inferir qual DTO Filter usar para filtros de listagem."""
    entity = _path_to_entity_name(path)
    for s in schemas_list:
        if entity and s['name'].startswith(entity):
            if s['name'].endswith('Filter'):
                return s['name']
    for s in schemas_list:
        if s['name'].endswith('Filter'):
            return s['name']
    return None


def _is_filter_field(field):
    """Verifica se um campo parece ser filtravel."""
    exclude_names = {'id', 'codigo'}
    # Excluir por nome exato
    if field['name'].lower() in exclude_names:
        return False
    # Excluir por sufixo (campos de configuracao, nao filtro)
    exclude_suffixes = ('casasDecimais', 'CasasDecimais', 'criterioAproximacao',
                        'CriterioAproximacao', 'valor', 'Valor', 'quantidade',
                        'Quantidade')
    for suffix in exclude_suffixes:
        if field['name'].endswith(suffix):
            return False
    # Apenas campos filteraveis: string, boolean, integer (exceto id)
    return field['type'] in ('string', 'boolean', 'integer')


def _infer_filter_fields(schemas_list, path):
    """Obtem campos de filtro para query parameters (GET list)."""
    # Primeiro tentar Filter DTO explicito
    filter_name = _infer_filter_dto(schemas_list, path)
    if filter_name:
        for s in schemas_list:
            if s['name'] == filter_name:
                return [f for f in s['fields'] if _is_filter_field(f)]

    # Fallback: inferir campos filtravel do entity Input/Output
    entity = _path_to_entity_name(path)
    for s in schemas_list:
        if entity and s['name'].startswith(entity) and not s['name'].endswith('Filter'):
            return [f for f in s['fields'] if _is_filter_field(f)]
    return []


def _build_filter_example(filter_fields):
    """Gera texto de exemplo de filtro a partir dos campos."""
    if not filter_fields:
        return ""
    parts = []
    for f in filter_fields[:4]:
        if f['type'] == 'string':
            parts.append(f"{f['name']}=exemplo")
        elif f['type'] == 'boolean':
            parts.append(f"{f['name']}=true")
        elif f['type'] == 'integer':
            parts.append(f"{f['name']}=0")
    if len(filter_fields) > 4:
        parts.append("...")
    query_str = '&'.join(parts)
    return f"""

**Filtros disponiveis:**
| Parametro | Tipo | Descricao |
|-----------|------|-----------|
""" + '\n'.join(
    f"| {f['name']} | {f['type']} | {_field_name_to_description(f['name'])} |"
    for f in filter_fields
) + f"""

**Exemplo de uso:**
```
?{query_str}
```"""


def main():
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} TICKET_DIR", file=sys.stderr)
        sys.exit(1)

    ticket_dir = sys.argv[1].rstrip('/')
    ticket_id = os.path.basename(ticket_dir)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    reveal_dir = os.path.join(script_dir, '..')

    # Carregar dados
    tasks_file = os.path.join(ticket_dir, 'status-tasks.json')
    jira_file = os.path.join(ticket_dir, 'jira-data.json')
    desc_file = os.path.join(ticket_dir, 'description.md')

    tasks_data = load_json(tasks_file)
    ticket_data = load_json(jira_file)
    tasks = tasks_data.get('tarefas', [])

    enriched_desc = ""
    if os.path.exists(desc_file):
        with open(desc_file) as f:
            enriched_desc = f.read()

    projetos = detect_projects(ticket_dir)
    project_name = projetos[0] if projetos else ''

    project_config = load_project_config(reveal_dir, project_name)
    project_context = load_project_context(reveal_dir, project_name)

    needs_api = detect_api_endpoints_needed(ticket_data, tasks) or detect_task_api_involvement(tasks)

    if not needs_api:
        if not enriched_desc:
            print(f"INFO: Ticket {ticket_id} nao parece envolver API. Nenhum openapi.yaml gerado.", file=sys.stderr)
            return

    endpoints = extract_endpoints_from_tasks(tasks, project_context)
    desc_endpoints, desc_schemas = extract_description_sections(enriched_desc)
    endpoints.extend(desc_endpoints)

    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = (ep['method'].lower(), ep['path'])
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)

    schemas = {}
    for t in tasks:
        obs = t.get('observacoes', '')
        task_schemas = extract_dtos_from_obs(obs)
        schemas.update(task_schemas)

    schemas.update(desc_schemas)

    project_path = project_config.get('path', '')
    if project_path:
        if not os.path.isabs(project_path):
            project_path = os.path.join(reveal_dir, project_path)
        base_pkg = detect_base_package(project_path)
        source_schemas = scan_source_dtos(project_path, base_pkg)

        entity_roots = _derive_entity_roots(unique_endpoints, tasks, schemas)
        filtered = {}
        for name, data in source_schemas.items():
            if _is_relevant_schema(name, entity_roots):
                filtered[name] = data
        source_schemas = filtered
        schemas.update(source_schemas)

    summary = ticket_data.get('basic', {}).get('summary', '') or ticket_data.get('summary', '')
    api_base_url = project_config.get('apiBaseUrl', '')
    api_tags = project_context.get('api_tags', [])

    for ep in unique_endpoints:
        if not ep['tags'] and api_tags:
            for tag in api_tags:
                if tag['name'].lower() in ep['path'].lower():
                    ep['tags'] = [tag['name']]
                    break
            if not ep['tags']:
                ep['tags'] = [api_tags[0]['name']]

    schemas_list = []
    for name, schema_data in schemas.items():
        schemas_list.append({
            'name': name,
            'fields': schema_data.get('fields', []),
        })

    paths_grouped = defaultdict(list)
    for ep in unique_endpoints:
        paths_grouped[ep['path']].append({
            'method': ep['method'],
            'operationId': ep['operationId'],
            'summary': ep['summary'],
            'tags': ep['tags'],
            'parameters': ep['parameters'],
            'requestBody': ep.get('requestBody'),
            'responses': ep.get('responses', []),
        })

    paths_list = [{'path': p, 'methods': m} for p, m in sorted(paths_grouped.items())]

    date_str = datetime.now().strftime('%Y-%m-%d')

    spec = _build_openapi_spec(
        ticket_id=ticket_id,
        summary=summary or ticket_id,
        date=date_str,
        api_base_url=api_base_url,
        api_tags=api_tags,
        paths_grouped=paths_list,
        schemas_list=schemas_list,
        project_name=project_name,
    )

    # Gerar openapi.yaml
    yaml_path = os.path.join(ticket_dir, 'openapi.yaml')
    try:
        import yaml
        with open(yaml_path, 'w') as f:
            yaml.dump(spec, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
        print(f"openapi.yaml gerado em {yaml_path}", file=sys.stderr)
    except ImportError:
        print(f"AVISO: pyyaml nao instalado, pulando openapi.yaml", file=sys.stderr)

    result = {
        'ticket_id': ticket_id,
        'endpoints': len(unique_endpoints),
        'schemas': len(schemas),
        'yaml': yaml_path,
    }
    print(json.dumps(result))


def detect_base_package(project_path):
    """Detecta pacote base do projeto."""
    agents_path = os.path.join(project_path, 'AGENTS.md')
    if os.path.exists(agents_path):
        with open(agents_path) as f:
            for line in f:
                m = re.search(r'base.*pacote.*[:\s]+([\w.]+)', line, re.IGNORECASE)
                if m:
                    return m.group(1)

    pom_path = os.path.join(project_path, 'pom.xml')
    if os.path.exists(pom_path):
        with open(pom_path) as f:
            content = f.read()
            m = re.search(r'<groupId>([\w.]+)</groupId>', content)
            if m:
                return m.group(1)

    return 'com.maps.dataa.tesouraria'


def extract_observacoes_text(tasks):
    """Extrai texto consolidado das observacoes."""
    texts = []
    for t in tasks:
        obs = t.get('observacoes', '')
        if obs:
            texts.append(obs)
    return '\n\n'.join(texts)


if __name__ == '__main__':
    main()
