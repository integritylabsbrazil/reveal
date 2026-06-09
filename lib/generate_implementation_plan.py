#!/usr/bin/env python3
"""Gera implementation-plan.md rico a partir de jira-data, impact-report, status-tasks.

Uso: python3 generate_implementation_plan.py TICKET_DIR
"""

import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import load_json, get_custom_field, detect_base_package


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


def try_read_source_file(filepath, max_lines=80):
    """Tenta ler um arquivo fonte e retorna o conteudo ou None."""
    try:
        if not os.path.isfile(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        content_lines = []
        started = False
        brace_depth = 0
        saw_opening_brace = False
        for line in lines:
            stripped = line.strip()
            if not started:
                if stripped.startswith('@') or stripped.startswith('public class') or \
                   stripped.startswith('@Entity') or stripped.startswith('@RestController') or \
                   stripped.startswith('@Service') or stripped.startswith('@Data') or \
                   stripped.startswith('public record') or stripped.startswith('public interface') or \
                   stripped.startswith('public enum'):
                    started = True
                continue
            content_lines.append(line)
            brace_depth += line.count('{') - line.count('}')
            if line.count('{') > 0:
                saw_opening_brace = True
            if brace_depth <= 0 and saw_opening_brace and len(content_lines) > 3:
                break
            if len(content_lines) >= max_lines:
                break
        result = ''.join(content_lines[:max_lines])
        if result.strip() and not result.strip().endswith('}'):
            result += '\n    // ...'
        return result.strip()
    except Exception:
        return None


def find_code_examples(project_path, scan_data, project_sections=None):
    """Encontra e le arquivos de exemplo no projeto via contexto ou scan."""
    examples = {'controller': None, 'service': None, 'entity': None, 'dto': None}

    if not project_path or not os.path.isdir(project_path):
        return examples

    src_main = os.path.join(project_path, 'src', 'main', 'java')
    if not os.path.isdir(src_main):
        # Tentar src/ se nao for Java
        alt_src = os.path.join(project_path, 'src')
        if os.path.isdir(alt_src):
            src_main = alt_src
        else:
            return examples

    # Construir caminhos de exemplo a partir do projects-context
    ctx_paths = {}

    if project_sections:
        # Extrair caminhos das secoes de padroes
        for sec_name, prefix in [('Padroes de Controllers', 'controller'),
                                  ('Padroes de Services', 'service'),
                                  ('Padroes de Entities', 'entity'),
                                  ('Padroes de DTOs', 'dto')]:
            if sec_name in project_sections:
                content = project_sections[sec_name]
                for line in content.split('\n'):
                    # Formato: `pacote.Classe` -- `caminho/relativo`
                    if '` -- `' in line or '\u2014' in line:
                        separator = ' -- ' if ' -- ' in line else ' \u2014 '
                        parts = line.split(separator, 1)
                        if len(parts) == 2:
                            path_part = parts[1].strip().strip('`')
                            full_path = os.path.join(project_path, path_part.replace('/', os.sep))
                            if os.path.isfile(full_path):
                                content_read = try_read_source_file(full_path)
                                if content_read:
                                    rel = path_part.replace(str(project_path) + '/', '')
                                    if prefix == 'controller' and not examples['controller']:
                                        examples['controller'] = {'path': rel, 'content': content_read}
                                        ctx_paths['controller'] = rel
                                    elif prefix == 'service' and not examples['service']:
                                        examples['service'] = {'path': rel, 'content': content_read}
                                        ctx_paths['service'] = rel
                                    elif prefix == 'entity' and not examples['entity']:
                                        examples['entity'] = {'path': rel, 'content': content_read}
                                        ctx_paths['entity'] = rel
                                    elif prefix == 'dto' and (not examples['dto'] or len(examples['dto']) < 2):
                                        if not examples['dto']:
                                            examples['dto'] = []
                                        typ = 'Input' if 'Input' in path_part else ('Output' if 'Output' in path_part else 'DTO')
                                        examples['dto'].append({'path': rel, 'content': content_read, 'type': typ})
                                        ctx_paths[f'dto_{typ.lower()}'] = rel

    # Fallback: caminhos hardcoded antigos (se projects-context nao existir)
    if not ctx_paths:
        fallback_paths = {
            'controller': ['controller/'],
            'service': ['service/'],
            'entity': ['domain/', 'entity/'],
            'dto': ['model/', 'dto/'],
        }
        for root, dirs, files in os.walk(src_main):
            for f in files:
                if f.endswith('.java') or f.endswith('.ts') or f.endswith('.tsx'):
                    rel = os.path.relpath(os.path.join(root, f), src_main)
                    for key, patterns in fallback_paths.items():
                        if any(p in rel for p in patterns):
                            if key == 'controller' and not examples['controller']:
                                content = try_read_source_file(os.path.join(root, f))
                                if content:
                                    examples['controller'] = {'path': rel, 'content': content}
                            elif key == 'service' and not examples['service']:
                                content = try_read_source_file(os.path.join(root, f))
                                if content:
                                    examples['service'] = {'path': rel, 'content': content}
                            elif key == 'entity' and not examples['entity']:
                                content = try_read_source_file(os.path.join(root, f))
                                if content:
                                    examples['entity'] = {'path': rel, 'content': content}

    return examples


def _extract_html_fields(html_text):
    """Extrai campos de texto HTML com estrutura <li>Campo: NOME<ul><li>...</li></ul>."""
    fields = []
    if not html_text:
        return fields

    # Encontrar todas as posicoes de '<li>Campo:'
    positions = [m.end() for m in re.finditer(r'<li[^>]*>\s*Campo:\s*', html_text, re.IGNORECASE)]

    for i, pos in enumerate(positions):
        # Extrair nome do campo (do final de 'Campo: ' ate o proximo < ou \n)
        rest = html_text[pos:]
        name_match = re.match(r'([^<\n]+)', rest)
        if not name_match:
            continue
        name = name_match.group(1).strip().rstrip(':').strip()
        if not name:
            continue

        # Encontrar o bloco de detalhes: procurar <ul> mais proximo
        # e extrair ate o </ul> correspondente (contando nesting)
        ul_start = rest.find('<ul>')
        if ul_start < 0:
            continue

        ul_content_start = ul_start + 4
        depth = 1
        ul_end = ul_content_start
        while depth > 0 and ul_end < len(rest):
            next_open = rest.find('<ul>', ul_end)
            next_close = rest.find('</ul>', ul_end)
            if next_close < 0:
                break
            if next_open >= 0 and next_open < next_close:
                depth += 1
                ul_end = next_open + 4
            else:
                depth -= 1
                ul_end = next_close + 5

        details_html = rest[ul_content_start:ul_end - 5] if depth == 0 else ''

        detail_items = re.findall(r'<li>(.*?)</li>', details_html, re.DOTALL)
        details = []
        for item in detail_items:
            clean = re.sub(r'<[^>]+>', '', item).strip()
            if clean:
                details.append(clean)

        field = {
            'name': name,
            'details': details,
            'type': _infer_type(details),
            'required': any('brigató' in d for d in details),
            'values': _extract_values(details),
        }
        fields.append(field)

    return fields


def parse_fields_from_requirements_html(html_text):
    """Extrai definicoes de campos de requisitos a partir de texto HTML ou plain."""
    if not html_text:
        return []

    fields = _extract_html_fields(html_text)

    # Tentativa 2: Plain text format ("Campo: NOME\n- detalhe\n- detalhe")
    if not fields:
        # Buscar "Campo: NOME" seguido de linhas com detalhes
        campo_blocks = re.split(r'\n\s*(?=Campo:\s)', html_text)
        for block in campo_blocks:
            if not block.strip().startswith('Campo:'):
                continue
            lines = block.strip().split('\n')
            if not lines:
                continue
            name = lines[0].replace('Campo:', '').strip().rstrip(':')
            details = []
            for line in lines[1:]:
                clean = line.strip().lstrip('-*•').strip()
                if clean:
                    details.append(clean)
            if name:
                field = {
                    'name': name,
                    'details': details,
                    'type': _infer_type(details),
                    'required': any('brigató' in d for d in details),
                    'values': _extract_values(details),
                }
                fields.append(field)

    return fields


def _infer_type(details):
    """Tenta inferir o tipo do campo a partir dos detalhes."""
    full = ' '.join(details).lower()
    if 'autocomplete' in full or 'sele' in full:
        if 'checkbox' in full:
            return 'Lista (checkbox)'
        return 'Autocomplete'
    if 'numérico' in full or 'numerico' in full or 'números' in full or 'numeros' in full or 'inteiros' in full:
        return 'Integer'
    if 'decimal' in full:
        return 'BigDecimal'
    return 'String'


def _extract_values(details):
    """Extrai valores enumerados dos detalhes."""
    values = []
    full = ' '.join(details)
    # Padrao: "Valores disponiveis: ..." seguido de <ul><li>
    values_match = re.search(r'Valores dispon[íi]veis[:\s]*(.*?)(?:<|$)', full, re.IGNORECASE)
    if values_match:
        # Extrair itens de lista
        items = re.findall(r'<li>(.*?)</li>', values_match.group(1), re.DOTALL)
        if items:
            values = [re.sub(r'<[^>]+>', '', i).strip() for i in items]
        else:
            # Fallback: split por virgula
            parts = re.sub(r'<[^>]+>', '', values_match.group(1)).strip().split(',')
            values = [p.strip() for p in parts if p.strip()]
    return values


def build_entity_field_table(fields, entity_name, table_name):
    """Gera tabela de campos de entidade JPA."""
    if not fields:
        return ''

    lines = [f'### {entity_name}']
    lines.append('')
    lines.append(f'**Tabela:** `{table_name}`')
    lines.append('')
    lines.append('| Campo | Coluna | Tipo | Tamanho | Obrigatório | Descrição |')
    lines.append('|-------|--------|------|---------|-------------|-----------|')
    for f in fields:
        col = _to_column_name(f['name'])
        typ = f.get('type', 'String')
        size = '255'
        if typ == 'Integer':
            size = '-'
        elif typ == 'BigDecimal':
            size = '18,6'
        req = 'Sim' if f.get('required', False) else 'Não'
        desc = f['details'][0] if f['details'] else ''
        lines.append(f'| {f["name"]} | {col} | {typ} | {size} | {req} | {desc} |')
    lines.append('')
    return '\n'.join(lines)


def build_dto_table(fields, dto_name):
    """Gera tabela de campos de DTO."""
    if not fields:
        return ''

    lines = [f'### {dto_name}']
    lines.append('')
    lines.append('| Campo | Tipo | Obrigatório | Validação |')
    lines.append('|-------|------|-------------|-----------|')
    for f in fields:
        typ = f.get('type', 'String')
        req = 'Sim' if f.get('required', False) else 'Não'
        vals = f.get('values', [])
        validation = f'@NotNull' if f.get('required', False) else ''
        if vals:
            validation += f' @Pattern(regexp="{"|".join(vals)}")' if not validation else f'\nValores: {", ".join(vals)}'
        lines.append(f'| {f["name"]} | {typ} | {req} | {validation} |')
    lines.append('')
    return '\n'.join(lines)


def build_migration_table(fields, table_name, sequence_name):
    """Gera tabela de migracao Liquibase."""
    if not fields:
        return ''

    lines = [f'### Liquibase — {table_name}']
    lines.append('')
    lines.append(f'**Sequence:** `{sequence_name}`')
    lines.append('')
    lines.append('```xml')
    lines.append(f'<changeSet id="1" author="reveal">')
    lines.append(f'    <createSequence sequenceName="{sequence_name}"/>')
    lines.append(f'    <createTable tableName="{table_name}">')
    lines.append(f'        <column name="ID" type="BIGINT">')
    lines.append(f'            <constraints primaryKey="true" nullable="false"/>')
    lines.append(f'        </column>')
    for f in fields:
        col = _to_column_name(f['name'])
        typ = _java_to_sql_type(f.get('type', 'String'))
        nullable = 'false' if f.get('required', False) else 'true'
        lines.append(f'        <column name="{col}" type="{typ}">')
        lines.append(f'            <constraints nullable="{nullable}"/>')
        lines.append(f'        </column>')
    lines.append(f'        <column name="ATIVO" type="BOOLEAN" defaultValueBoolean="true">')
    lines.append(f'            <constraints nullable="false"/>')
    lines.append(f'        </column>')
    lines.append(f'    </createTable>')
    lines.append(f'</changeSet>')
    lines.append('```')
    lines.append('')
    return '\n'.join(lines)


def _to_column_name(name):
    """Converte nome de campo para nome de coluna SQL (SNAKE_CASE)."""
    # "Quantidade casas decimais" -> "QTDE_CASAS_DECIMAIS"
    # Primeiro, transliterar acentos
    trans = str.maketrans({
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
        'Ç': 'C', 'Ã': 'A', 'Õ': 'O', 'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
    })
    clean = name.translate(trans)
    # Remover sufixos comuns de entidade
    clean = re.sub(r'\b(Contábil|Contabil)\b', 'CONT', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(Patrimonial)\b', 'PATRIM', clean, flags=re.IGNORECASE)
    # Split por espaco, uppercase, join com underscore
    parts = clean.split()
    if len(parts) <= 2:
        return '_'.join(p.upper() for p in parts)
    # Para nomes longos, abreviar
    abbr = []
    for p in parts:
        if p.upper() in ('DE', 'DA', 'DO', 'EM', 'NO', 'NA', 'PARA', 'COM', 'E'):
            continue
        if len(p) > 5:
            abbr.append(p[:5].upper())
        else:
            abbr.append(p.upper())
    return '_'.join(abbr)


def _java_to_sql_type(java_type):
    mapping = {
        'Integer': 'INTEGER',
        'BigDecimal': 'NUMERIC(18,6)',
        'Autocomplete': 'VARCHAR(255)',
        'Lista (checkbox)': 'VARCHAR(4000)',
        'String': 'VARCHAR(255)',
    }
    return mapping.get(java_type, 'VARCHAR(255)')


# ---------------------------------------------------------------------------
# Geracao de codigo Java concreto (skeletons executaveis)
# ---------------------------------------------------------------------------


def _name_to_field_name(display_name):
    """Converte nome de exibicao para nome de campo Java (camelCase).
    Ex: 'Quantidade casas decimais' -> 'quantidadeCasasDecimais'
    """
    trans = str.maketrans({
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'Ç': 'C',
        ' ': '_',
    })
    clean = display_name.translate(trans)
    parts = clean.lower().split('_')
    if not parts:
        return 'campo'
    result = parts[0]
    for p in parts[1:]:
        if p:
            result += p[0].upper() + p[1:]
    return result


def _name_to_class_name(display_name):
    """Converte nome de exibicao para nome de classe Java (PascalCase).
    Ex: 'Parametro Cota Patrimonial' -> 'ParametroCotaPatrimonial'
    """
    trans = str.maketrans({
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'Ç': 'C',
    })
    clean = display_name.translate(trans)
    parts = clean.replace('_', ' ').split()
    return ''.join(p.capitalize() for p in parts if p)


def _get_validation_annotations(field):
    """Retorna lista de anotacoes de validacao para um campo."""
    anns = []
    if field.get('required', False):
        if field.get('type') == 'String' or 'texto' in str(field.get('details', [])).lower():
            anns.append('@NotBlank')
        elif field.get('type') in ('Integer', 'BigDecimal', 'Autocomplete'):
            anns.append('@NotNull')
    # Verificar valores maximos/minimos nas descricoes
    details = ' '.join(field.get('details', []))
    max_match = re.search(r'at[ée]\s+(\d+)', details)
    if max_match:
        max_val = max_match.group(1)
        anns.append(f'@Max({max_val})')
    min_match = re.search(r'm[ií]nimo\s+(\d+)', details, re.IGNORECASE)
    if min_match:
        min_val = min_match.group(1)
        anns.append(f'@Min({min_val})')
    return anns


def _java_type(field_type):
    """Mapeia tipo inferido para tipo Java."""
    mapping = {
        'Integer': 'Integer',
        'BigDecimal': 'BigDecimal',
        'Autocomplete': 'String',
        'Lista (checkbox)': 'String',
        'String': 'String',
        'Boolean': 'Boolean',
        'Date': 'LocalDate',
        'DateTime': 'LocalDateTime',
    }
    return mapping.get(field_type, 'String')


def build_entity_code(fields, entity_name, table_name, pkg):
    """Gera codigo Java completo de uma entidade JPA."""
    if not fields:
        return ''
    class_name = _name_to_class_name(entity_name)
    lines = [f'package {pkg}.domain;', '']
    lines.append('import javax.persistence.*;')
    lines.append('import lombok.Data;')
    lines.append('import lombok.NoArgsConstructor;')
    lines.append('import lombok.AllArgsConstructor;')
    lines.append('import lombok.Builder;')
    lines.append('')
    lines.append('@Entity')
    lines.append(f'@Table(name = "{table_name}")')
    lines.append('@Data')
    lines.append('@NoArgsConstructor')
    lines.append('@AllArgsConstructor')
    lines.append('@Builder')
    lines.append(f'public class {class_name} {{')
    lines.append('')
    lines.append('    @Id')
    lines.append(f'    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "SEQ_{table_name}")')
    lines.append(f'    @SequenceGenerator(name = "SEQ_{table_name}", sequenceName = "SEQ_{table_name}", allocationSize = 1)')
    lines.append('    private Long id;')
    lines.append('')
    for f in fields:
        java_type = _java_type(f.get('type', 'String'))
        field_name = _name_to_field_name(f['name'])
        col_name = _to_column_name(f['name'])
        nullable = '' if f.get('required', True) else ' nullable = true'
        lines.append(f'    @Column(name = "{col_name}"{nullable})')
        lines.append(f'    private {java_type} {field_name};')
        lines.append('')
    lines.append('    @Column(name = "ATIVO", nullable = false)')
    lines.append('    private Boolean ativo = true;')
    lines.append('}')
    return '\n'.join(lines)


def build_input_dto_code(fields, dto_name, pkg):
    """Gera codigo Java completo de um DTO de input."""
    if not fields:
        return ''
    class_name = _name_to_class_name(dto_name) + 'Input'
    lines = [f'package {pkg}.model;', '']
    lines.append('import javax.validation.constraints.*;')
    lines.append('import lombok.Data;')
    lines.append('')
    lines.append('@Data')
    lines.append(f'public class {class_name} {{')
    lines.append('')
    for f in fields:
        java_type = _java_type(f.get('type', 'String'))
        field_name = _name_to_field_name(f['name'])
        anns = _get_validation_annotations(f)
        lines.append('')
        for ann in anns:
            lines.append(f'    {ann}')
        lines.append(f'    private {java_type} {field_name};')
    lines.append('')
    lines.append('}')
    return '\n'.join(lines)


def build_repository_code(entity_name, pkg):
    """Gera codigo Java completo de um repository Spring Data."""
    class_name = _name_to_class_name(entity_name)
    lines = [f'package {pkg}.repository;', '']
    lines.append('import org.springframework.data.jpa.repository.JpaRepository;')
    lines.append('import org.springframework.stereotype.Repository;')
    lines.append(f'import {pkg}.domain.{class_name};')
    lines.append('')
    lines.append('@Repository')
    lines.append(f'public interface {class_name}Repository extends JpaRepository<{class_name}, Long> {{')
    lines.append('')
    lines.append('}')
    return '\n'.join(lines)


def build_service_skeleton(entity_name, pkg):
    """Gera esqueleto de service com metodos CRUD."""
    class_name = _name_to_class_name(entity_name)
    entity_var = class_name[0].lower() + class_name[1:]
    lines = [f'package {pkg}.service;', '']
    lines.append('import lombok.RequiredArgsConstructor;')
    lines.append('import lombok.extern.slf4j.Slf4j;')
    lines.append('import org.springframework.stereotype.Service;')
    lines.append('import org.springframework.transaction.annotation.Transactional;')
    lines.append(f'import {pkg}.domain.{class_name};')
    lines.append(f'import {pkg}.repository.{class_name}Repository;')
    lines.append('')
    lines.append('@Service')
    lines.append('@Slf4j')
    lines.append('@RequiredArgsConstructor')
    lines.append(f'public class {class_name}Service {{')
    lines.append('')
    lines.append(f'    private final {class_name}Repository repository;')
    lines.append('')
    lines.append(f'    @Transactional(readOnly = true)')
    lines.append(f'    public List<{class_name}> listar() {{')
    lines.append(f'        return repository.findAll();')
    lines.append(f'    }}')
    lines.append('')
    lines.append(f'    @Transactional(readOnly = true)')
    lines.append(f'    public {class_name} buscarPorId(Long id) {{')
    lines.append(f'        return repository.findById(id)')
    lines.append(f'                .orElseThrow(() -> new RuntimeException("{class_name} nao encontrado: " + id));')
    lines.append(f'    }}')
    lines.append('')
    lines.append(f'    @Transactional')
    lines.append(f'    public {class_name} criar({class_name} entity) {{')
    lines.append(f'        log.info("Criando {class_name}: {{}}", entity);')
    lines.append(f'        return repository.save(entity);')
    lines.append(f'    }}')
    lines.append('')
    lines.append(f'    @Transactional')
    lines.append(f'    public {class_name} atualizar(Long id, {class_name} entity) {{')
    lines.append(f'        buscarPorId(id);')
    lines.append(f'        entity.setId(id);')
    lines.append(f'        return repository.save(entity);')
    lines.append(f'    }}')
    lines.append('')
    lines.append(f'    @Transactional')
    lines.append(f'    public void excluir(Long id) {{')
    lines.append(f'        {class_name} entity = buscarPorId(id);')
    lines.append(f'        repository.delete(entity);')
    lines.append(f'        log.info("{class_name} excluido: {{}}", id);')
    lines.append(f'    }}')
    lines.append('')
    lines.append('}')
    return '\n'.join(lines)


def build_controller_code(entity_name, pkg, endpoint_path):
    """Gera codigo Java completo de um controller REST."""
    class_name = _name_to_class_name(entity_name) + 'Controller'
    service_name = _name_to_class_name(entity_name) + 'Service'
    entity_class = _name_to_class_name(entity_name)
    if not endpoint_path:
        endpoint_path = '/' + _name_to_field_name(entity_name).lower().replace('_', '-')
    lines = [f'package {pkg}.controller;', '']
    lines.append('import lombok.RequiredArgsConstructor;')
    lines.append('import org.springframework.http.HttpStatus;')
    lines.append('import org.springframework.http.ResponseEntity;')
    lines.append('import org.springframework.web.bind.annotation.*;')
    lines.append(f'import {pkg}.domain.{entity_class};')
    lines.append(f'import {pkg}.service.{service_name};')
    lines.append('import javax.validation.Valid;')
    lines.append('import java.util.List;')
    lines.append('')
    lines.append('@RestController')
    lines.append(f'@RequestMapping("{endpoint_path}")')
    lines.append('@RequiredArgsConstructor')
    lines.append(f'public class {class_name} {{')
    lines.append('')
    lines.append(f'    private final {service_name} service;')
    lines.append('')
    lines.append('    @GetMapping')
    lines.append(f'    public ResponseEntity<List<{entity_class}>> listar() {{')
    lines.append(f'        return ResponseEntity.ok(service.listar());')
    lines.append(f'    }}')
    lines.append('')
    lines.append(f'    @GetMapping("/{{id}}")')
    lines.append(f'    public ResponseEntity<{entity_class}> buscarPorId(@PathVariable Long id) {{')
    lines.append(f'        return ResponseEntity.ok(service.buscarPorId(id));')
    lines.append(f'    }}')
    lines.append('')
    lines.append('    @PostMapping')
    lines.append(f'    public ResponseEntity<{entity_class}> criar(@Valid @RequestBody {entity_class} input) {{')
    lines.append(f'        return ResponseEntity.status(HttpStatus.CREATED).body(service.criar(input));')
    lines.append(f'    }}')
    lines.append('')
    lines.append(f'    @PutMapping("/{{id}}")')
    lines.append(f'    public ResponseEntity<{entity_class}> atualizar(@PathVariable Long id, @Valid @RequestBody {entity_class} input) {{')
    lines.append(f'        return ResponseEntity.ok(service.atualizar(id, input));')
    lines.append(f'    }}')
    lines.append('')
    lines.append(f'    @DeleteMapping("/{{id}}")')
    lines.append(f'    public ResponseEntity<Void> excluir(@PathVariable Long id) {{')
    lines.append(f'        service.excluir(id);')
    lines.append(f'        return ResponseEntity.noContent().build();')
    lines.append(f'    }}')
    lines.append('')
    lines.append('}')
    return '\n'.join(lines)


def build_jira_block(ticket_id, summary, fields, tasks):
    """Gera bloco de texto formatado para copiar para o Jira."""
    if not fields:
        return ''
    lines = []
    lines.append('<!-- ===== COPIAR PARA O JIRA ===== -->')
    lines.append('')
    lines.append(f'h3. {ticket_id} — {summary}')
    lines.append('')
    lines.append('----')
    lines.append('')

    # Tasks
    lines.append('h4. Subtarefas')
    lines.append('')
    for t in tasks:
        lines.append(f'* *{t["id"]} — {t.get("nivel", "")}*: {t["descricao"]}')
    lines.append('')

    # Fields per domain
    if fields:
        cota_keywords = ['quantidade', 'critério', 'criterio', 'decimal', 'aproximação', 'aproximac']
        cota_fields = [f for f in fields if any(k in f['name'].lower() for k in cota_keywords)]
        geral_fields = [f for f in fields if f not in cota_fields]

        # Deduplicar geral_fields
        seen_names = set()
        deduped_geral = []
        for f in geral_fields:
            if f['name'].lower() not in seen_names:
                seen_names.add(f['name'].lower())
                deduped_geral.append(f)
        geral_fields = deduped_geral

        # Usar somente os campos especificos do cota (QtdDecimal, Criterio)
        # para o grupo Parâmetro Cota (nao incluir Balancete/Perfil duplicados)
        # O usuario vera Balancete/Perfil no contexto da aba 1

        for group_name, group_fields in [
            ('Parametrização Contábil (Aba 1)', geral_fields),
            ('Parâmetro Cotas (Aba 2)', cota_fields),
        ]:
            if group_fields:
                lines.append(f'h4. Campos — {group_name}')
                lines.append('')
                lines.append('|| Campo || Tipo || Obrigatório || Observação ||')
                for f in group_fields:
                    typ = f.get('type', 'String')
                    req = 'Sim' if f.get('required', False) else 'Não'
                    obs = f['details'][0] if f['details'] else ''
                    lines.append(f'| {f["name"]} | {typ} | {req} | {obs} |')
                lines.append('')

    lines.append('----')
    lines.append('')
    lines.append('h4. Observações Técnicas')
    lines.append('')
    lines.append(f'* Stack: Spring Boot 2.7.4 / Java 11 / PostgreSQL / Liquibase')
    lines.append(f'* Padrão: Package-by-Feature (controller/service/domain/repository)')
    lines.append(f'* Lombok + MapStruct para redução de boilerplate')
    lines.append(f'* Ações em classes separadas (GetAction/CreateAction/ValidatorAction)')
    lines.append('')
    lines.append('<!-- ===== FIM ===== -->')
    return '\n'.join(lines)


def build_code_block_section(examples):
    """Gera secao de exemplos de codigo com blocos de codigo."""
    if not examples:
        return ''

    parts = []
    parts.append('## Exemplos de Código do Projeto')
    parts.append('')
    parts.append('Os exemplos abaixo foram extraídos do código fonte real do projeto para referência:')
    parts.append('')

    if examples.get('entity'):
        ex = examples['entity']
        parts.append(f'### Entity — `{ex["path"]}`')
        parts.append('')
        parts.append('```java')
        parts.append(ex['content'])
        parts.append('```')
        parts.append('')

    if examples.get('dto'):
        for dto in examples['dto']:
            parts.append(f'### DTO ({dto["type"]}) — `{dto["path"]}`')
            parts.append('')
            parts.append('```java')
            parts.append(dto['content'])
            parts.append('```')
            parts.append('')

    if examples.get('service'):
        ex = examples['service']
        parts.append(f'### Service — `{ex["path"]}`')
        parts.append('')
        parts.append('```java')
        parts.append(ex['content'])
        parts.append('```')
        parts.append('')

    if examples.get('controller'):
        ex = examples['controller']
        parts.append(f'### Controller — `{ex["path"]}`')
        parts.append('')
        parts.append('```java')
        parts.append(ex['content'])
        parts.append('```')
        parts.append('')

    return '\n'.join(parts)


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


def load_project_context(project_name, projects_ctx_dir):
    """Carrega projects-context/<projeto>.md e retorna secoes como dict."""
    ctx_file = os.path.join(projects_ctx_dir, f'{project_name}.md')
    if not os.path.isfile(ctx_file):
        return None
    with open(ctx_file, 'r') as f:
        content = f.read()
    sections = {}
    current_section = ''
    current_lines = []
    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_lines).strip()
            current_section = line.strip('## #').strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_section:
        sections[current_section] = '\n'.join(current_lines).strip()
    return sections


def extract_project_name(scan_data, tasks_data):
    """Tenta extrair nome do projeto a partir dos dados disponiveis."""
    # De scan_data
    if scan_data:
        name = scan_data.get('name', '')
        if name:
            return name
    # De tasks
    if tasks_data:
        projetos = tasks_data.get('projetosEnvolvidos', [])
        if projetos:
            return projetos[0]
    return ''


def find_projects_ctx_dir(ticket_dir):
    """Encontra o diretorio projects-context relativo ao reveal root."""
    # Ticket dir e como: reveal/tickets/TICKET_ID
    # Projects-context e: reveal/projects-context/
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(ticket_dir)), 'projects-context'),
        os.path.join(os.path.dirname(ticket_dir), '..', 'projects-context'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'projects-context'),
    ]
    for c in candidates:
        resolved = os.path.abspath(c)
        if os.path.isdir(resolved):
            return resolved
    return os.path.abspath(candidates[0])


def build_per_task_guide(tasks, project_sections, code_blocks_by_task=None):
    """Gera guia de implementacao por task usando observacoes reais, contexto do projeto
    e codigo Java concreto (skeletons) para tasks do tipo implementar/criar-classe.

    Args:
        tasks: lista de tasks de status-tasks.json
        project_sections: dict com secoes do contexto do projeto
        code_blocks_by_task: dict opcional {task_id: {entity_code, dto_input_code, repo_code, service_code, controller_code, migration_code}}
    """
    controller_examples = ''
    service_examples = ''
    entity_examples = ''
    dto_examples = ''
    pkg_examples = ''

    if project_sections:
        for sec, var in [('Padroes de Controllers', 'controller_examples'),
                          ('Padroes de Services', 'service_examples'),
                          ('Padroes de Entities', 'entity_examples'),
                          ('Padroes de DTOs', 'dto_examples')]:
            if sec in project_sections:
                s = project_sections[sec]
                lines = [l for l in s.split('\n') if '\u2014' in l][:3]
                if lines:
                    if var == 'controller_examples':
                        controller_examples = '\n'.join(lines)
                    elif var == 'service_examples':
                        service_examples = '\n'.join(lines)
                    elif var == 'entity_examples':
                        entity_examples = '\n'.join(lines)
                    elif var == 'dto_examples':
                        dto_examples = '\n'.join(lines)
        if 'Pacote Base' in project_sections:
            pkg_examples = project_sections['Pacote Base'].strip()

    code_blocks_by_task = code_blocks_by_task or {}

    parts = []
    for t in tasks:
        tid = t['id']
        desc = t.get('descricao', '')
        nivel = t.get('nivel', '')
        tipo = t.get('tipo', '')
        deps = t.get('dependeDe', [])
        observacoes = t.get('observacoes', '')
        jira_key = t.get('jiraKey', '')

        parts.append(f'### Task {tid} — {nivel}')
        if jira_key:
            parts.append(f'**Jira:** {jira_key}')
        parts.append('')
        parts.append(f'**Descricao:** {desc}')
        parts.append('')
        parts.append(f'**Tipo:** {tipo}')
        if deps:
            parts.append(f'**Depende de:** {", ".join(deps)}')
        parts.append('')

        if observacoes:
            parts.append('**Informacoes tecnicas para implementacao:**')
            parts.append('')
            parts.append('```')
            truncated_obs = observacoes[:6000]
            if len(observacoes) > 6000:
                truncated_obs += '\n... (observacoes truncadas — veja status-tasks.json para versao completa)'
            parts.append(truncated_obs)
            parts.append('```')
            parts.append('')

        # Codigo concreto (skeletons) para tasks implementar/criar
        if code_blocks_by_task.get(tid):
            cb = code_blocks_by_task[tid]

            if cb.get('migration_code'):
                parts.append('**Migration Liquibase:**')
                parts.append('')
                parts.append('```xml')
                parts.append(cb['migration_code'])
                parts.append('```')
                parts.append('')

            if cb.get('entity_code'):
                parts.append('**Entity — `{}.java`:**'.format(
                    _name_to_class_name(t.get('entity_name', 'Entity'))))
                parts.append('')
                parts.append('```java')
                parts.append(cb['entity_code'])
                parts.append('```')
                parts.append('')

            if cb.get('dto_input_code'):
                parts.append('**DTO Input:**')
                parts.append('')
                parts.append('```java')
                parts.append(cb['dto_input_code'])
                parts.append('```')
                parts.append('')

            if cb.get('dto_output_code'):
                parts.append('**DTO Output:**')
                parts.append('')
                parts.append('```java')
                parts.append(cb['dto_output_code'])
                parts.append('```')
                parts.append('')

            if cb.get('repository_code'):
                parts.append('**Repository:**')
                parts.append('')
                parts.append('```java')
                parts.append(cb['repository_code'])
                parts.append('```')
                parts.append('')

            if cb.get('service_code'):
                parts.append('**Service:**')
                parts.append('')
                parts.append('```java')
                parts.append(cb['service_code'])
                parts.append('```')
                parts.append('')

            if cb.get('controller_code'):
                parts.append('**Controller:**')
                parts.append('')
                parts.append('```java')
                parts.append(cb['controller_code'])
                parts.append('```')
                parts.append('')

        # Referencias do projeto (classes existentes como exemplo)
        if controller_examples:
            parts.append('**Controllers de referencia no projeto:**')
            parts.append(controller_examples)
            parts.append('')
        if service_examples:
            parts.append('**Services de referencia no projeto:**')
            parts.append(service_examples)
            parts.append('')
        if entity_examples:
            parts.append('**Entities de referencia no projeto:**')
            parts.append(entity_examples)
            parts.append('')
        if dto_examples:
            parts.append('**DTOs de referencia no projeto:**')
            parts.append(dto_examples)
            parts.append('')

        if pkg_examples:
            parts.append(f'**Pacote base:** `{pkg_examples}`')
            parts.append('')

        parts.append('---')
        parts.append('')

    return '\n'.join(parts)


def build_implementation_guide(project_sections):
    """Gera secao de guia de implementacao geral baseada no contexto."""
    if not project_sections:
        return ''

    parts = []
    parts.append('## Guia de Implementacao')
    parts.append('')
    parts.append('Baseado no codigo fonte do projeto e nos padroes identificados.')
    parts.append('')

    # Arquitetura
    if 'Arquitetura' in project_sections:
        arch = project_sections['Arquitetura']
        parts.append('### Arquitetura')
        parts.append('')
        parts.append(arch)
        parts.append('')

    # Convencoes — secoes com exemplos
    conv_sections = ['Padroes de Controllers', 'Padroes de Services',
                     'Padroes de Entities', 'Padroes de DTOs']
    for sec in conv_sections:
        if sec in project_sections:
            content = project_sections[sec]
            # Extrair anotacoes: linhas como - `Anotacao`
            ann_lines = [l for l in content.split('\n') if l.startswith('- `') and '`' in l][:8]
            # Extrair exemplos: linhas com `pkg.Classe` -- `path`
            ex_lines = [l for l in content.split('\n') if '\u2014' in l or '` -- `' in l][:3]
            parts.append(f'### {sec}')
            parts.append('')
            if ann_lines:
                parts.append('Anotacoes comuns:')
                for l in ann_lines:
                    parts.append(l)
                parts.append('')
            if ex_lines:
                parts.append('Exemplos:')
                for l in ex_lines:
                    parts.append(l)
                parts.append('')

    return '\n'.join(parts)


def build_prerequisites_section(tasks):
    """Gera secao de pre-requisitos por task."""
    parts = ['## Pre-requisitos por Task', '']
    for t in tasks:
        tid = t['id']
        desc = t.get('descricao', '')
        obs = t.get('observacoes', '')
        tipo = t.get('tipo', '')

        parts.append(f'### Task {tid} — {desc[:60]}')
        parts.append('')

        prereqs = []
        if t.get('dependeDe'):
            prereqs.append(f'Task(s) antecessora(s): {", ".join(t["dependeDe"])} concluida(s)')

        if 'criar' in tipo or 'implementar' in tipo:
            prereqs.append('Migration Liquibase aplicada no banco de dados alvo')
            prereqs.append('Sequence e tabela criadas no banco')

        if 'alterar' in tipo:
            prereqs.append('Codigo fonte existente localizado e analisado')
            prereqs.append('Testes existentes compilando antes das alteracoes')

        if 'migration' in obs.lower() or 'liquibase' in obs.lower():
            prereqs.append('Arquivo changelog XML criado no diretorio de migrations')
            prereqs.append('Ordem de execucao dos changesets respeitando o cronologico')

        if not prereqs:
            prereqs.append('Nenhum pre-requisito especifico identificado')

        for p in prereqs:
            parts.append(f'- [ ] {p}')
        parts.append('')

    return '\n'.join(parts)


def _safe_str(val):
    """Converte valor para string, tratando dicts/listas."""
    if isinstance(val, dict):
        return str(val)
    if isinstance(val, list):
        return ' '.join(str(v) for v in val)
    return str(val) if val is not None else ''

def build_config_section(tasks, jira_data):
    """Gera secao de configuracoes necessarias (application.yml, feature flags, env vars)."""
    text = ' '.join(filter(None, [
        _safe_str(jira_data.get('basic', {}).get('summary', '')),
        _safe_str(jira_data.get('basic', {}).get('description', '')),
        _safe_str(jira_data.get('customFields', {}).get('Requisitos Funcionais', '')),
    ]))
    text_lower = text.lower()

    parts = ['## Configuracoes Necessarias', '']

    has_config = any('config' in t.get('descricao', '').lower() or
                     'parametro' in t.get('descricao', '').lower() for t in tasks)

    if has_config or 'feature' in text_lower or 'toggle' in text_lower or 'flag' in text_lower:
        parts.append('### Feature Flags / Toggles')
        parts.append('')
        parts.append('| Flag | Descricao | Default |')
        parts.append('|------|-----------|---------|')
        parts.append('| feature.{dominio}.habilitado | Controla visibilidade da funcionalidade | false |')
        parts.append('')

    if 'application' in text_lower or 'yml' in text_lower or 'propriedade' in text_lower or has_config:
        parts.append('### application.yml / application-{env}.yml')
        parts.append('')
        parts.append('| Propriedade | Valor | Descricao |')
        parts.append('|-------------|-------|-----------|')
        parts.append('| app.{dominio}.casas-decimais | 4 | Quantidade de casas decimais (0-16) |')
        parts.append('| app.{dominio}.criterio-aproximacao | ARREDONDADO | Criterio: ARREDONDADO ou TRUNCADO |')
        parts.append('')

    if any('env' in t.get('descricao', '').lower() for t in tasks):
        parts.append('### Variaveis de Ambiente')
        parts.append('')
        parts.append('| Variavel | Descricao | Obrigatoria |')
        parts.append('|----------|-----------|-------------|')
        parts.append('| APP_DOMINIO_CONFIG | Configuracao de dominio | Sim |')
        parts.append('')

    if not any(keyword in text_lower for keyword in ['feature', 'toggle', 'flag', 'application', 'yml', 'propriedade', 'config']):
        parts.append('*Nenhuma configuracao especifica identificada nos requisitos.*')
        parts.append('')

    return '\n'.join(parts)


def build_rollback_section(tasks):
    """Gera secao de plano de rollback por task."""
    parts = ['## Plano de Rollback por Task', '']
    parts.append('| Task | Descricao | Comando de Rollback | Efeito |')
    parts.append('|------|-----------|--------------------|--------|')
    for t in tasks:
        tid = t['id']
        desc = t.get('descricao', '')[:50]
        cmd = t.get('rollbackCommand', 'git revert <hash> --no-edit')
        efeito = 'Reverte alteracoes da task'
        if 'migration' in t.get('tipo', '') or 'criar' in t.get('tipo', ''):
            efeito = 'Remove tabelas/entidades criadas'
        elif 'alterar' in t.get('tipo', ''):
            efeito = 'Restaura codigo ao estado anterior'
        parts.append(f'| {tid} | {desc} | `{cmd}` | {efeito} |')
    parts.append('')
    parts.append('> Nota: O `rollbackCommand` e valido ate o squash final da branch.')
    parts.append('')
    return '\n'.join(parts)


def build_security_section(tasks, jira_data):
    """Gera secao de seguranca e permissoes."""
    text = ' '.join(filter(None, [
        _safe_str(jira_data.get('basic', {}).get('summary', '')),
        _safe_str(jira_data.get('basic', {}).get('description', '')),
    ]))
    text_lower = text.lower()

    parts = ['## Seguranca e Permissoes', '']

    if any('admin' in t.get('descricao', '').lower() for t in tasks):
        parts.append('| Endpoint | Metodo | Roles |')
        parts.append('|----------|--------|-------|')
        parts.append('| /api/{dominio} | GET | TESOURARIA_CONSULTA |')
        parts.append('| /api/{dominio} | POST | TESOURARIA_ADMIN |')
        parts.append('| /api/{dominio}/{id} | PUT | TESOURARIA_ADMIN |')
        parts.append('| /api/{dominio}/{id} | DELETE | TESOURARIA_ADMIN |')
        parts.append('')

    if 'role' in text_lower or 'permissao' in text_lower or 'autoriza' in text_lower:
        parts.append('Roles mencionadas nos requisitos — confirmar com squad de seguranca.')
        parts.append('')

    parts.append('> **Nota:** Validar as permissoes com o squad de seguranca antes do deploy.')
    return '\n'.join(parts)


def build_config_section_from_scan(tasks, scan_data):
    """Gera seção de configurações baseada no scan do projeto."""
    if not scan_data:
        return ''
    docs = scan_data.get('projectDocs', {}) if isinstance(scan_data, dict) else {}
    readme = docs.get('readme', '') or ''
    parts = ['## Configuracoes do Projeto', '']
    if 'application.yml' in readme or 'application' in readme:
        parts.append('O projeto utiliza arquivos `application.yml` com perfis Spring.')
        parts.append('')
    return '\n'.join(parts) if len(parts) > 2 else ''


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

    # --- Carregar contexto do projeto ---
    project_name = extract_project_name(scan_data, tasks_data)
    projects_ctx_dir = find_projects_ctx_dir(ticket_dir)
    project_sections = load_project_context(project_name, projects_ctx_dir) if project_name else None
    if project_sections:
        print(f"[PLAN] Usando contexto do projeto: {project_name}", file=sys.stderr)

    # --- Carregar exemplos de codigo fonte ---
    project_path = None
    if tasks:
        pp = tasks[0].get('caminhoProjeto', '')
        if pp:
            # caminhoProjeto e relativo a raiz do reveal (pai de tickets/)
            reveal_root = os.path.normpath(os.path.join(ticket_dir, '..', '..'))
            project_path = os.path.normpath(os.path.join(reveal_root, pp))
            # Fallback: tentar relativo ao ticket_dir
            if not os.path.isdir(project_path):
                fallback = os.path.normpath(os.path.join(ticket_dir, pp))
                if os.path.isdir(fallback):
                    project_path = fallback
    code_examples = find_code_examples(project_path, scan_data, project_sections) if project_path else {}
    if code_examples and any(v for v in code_examples.values() if v):
        print(f"[PLAN] Exemplares de codigo carregados do projeto", file=sys.stderr)

    # --- Extrair campos dos requisitos ---
    req_fields = parse_fields_from_requirements_html(custom_text or '')

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

    # 3b. Guia de Implementacao (se contexto do projeto disponivel)
    if project_sections:
        guide = build_implementation_guide(project_sections)
        if guide:
            lines.append(guide)
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

    # 9b. Configuracoes Necessarias
    config_section = build_config_section(tasks, jira_data)
    if config_section:
        lines.append(config_section)
        lines.append('')

    # 9c. Pre-requisitos por Task
    prereqs_section = build_prerequisites_section(tasks)
    if prereqs_section:
        lines.append(prereqs_section)
        lines.append('')

    # 9d. Seguranca e Permissoes
    security_section = build_security_section(tasks, jira_data)
    if security_section:
        lines.append(security_section)
        lines.append('')

    # 10. Exemplos de Código (se disponível)
    code_section = build_code_block_section(code_examples)
    if code_section:
        lines.append(code_section)
        lines.append('')

    # 11. Gerar codigo concreto por task (skeletons)
    code_blocks_by_task = {}
    if req_fields:
        # Identificar campos para a primeira entidade (assumir que req_fields sao da entidade principal)
        main_fields = req_fields
        for t in tasks:
            if t.get('tipo') in ('implementar', 'criar-classe'):
                tid = t['id']
                entity_name = _name_to_class_name(domain_lower) if domain_lower else 'Entidade'
                table_name = _to_column_name(domain_lower) if domain_lower else 'ENTIDADE'
                cb = {}

                # Migration
                migration_text = build_migration_table(main_fields, table_name, f'SEQ_{table_name}')
                if migration_text:
                    # Extrair apenas o XML, nao as tabelas markdown
                    xml_match = re.search(r'```xml\n(.*?)```', migration_text, re.DOTALL)
                    if xml_match:
                        cb['migration_code'] = xml_match.group(1).strip()

                # Entity
                entity_code = build_entity_code(main_fields, entity_name, table_name, base_pkg)
                if entity_code:
                    cb['entity_code'] = entity_code
                    t['entity_name'] = entity_name

                # DTO Input
                dto_input = build_input_dto_code(main_fields, entity_name, base_pkg)
                if dto_input:
                    cb['dto_input_code'] = dto_input

                # DTO Output (builder style)
                dto_output_parts = [
                    f'package {base_pkg}.model;',
                    '',
                    'import lombok.Builder;',
                    'import lombok.Data;',
                    '',
                    '@Data',
                    '@Builder',
                    f'public class {_name_to_class_name(entity_name)}Output {{',
                    '    private Long id;',
                ]
                for f in main_fields:
                    java_type = _java_type(f.get('type', 'String'))
                    field_name = _name_to_field_name(f['name'])
                    dto_output_parts.append(f'    private {java_type} {field_name};')
                dto_output_parts.append('}')
                cb['dto_output_code'] = '\n'.join(dto_output_parts)

                # Repository
                repo_code = build_repository_code(entity_name, base_pkg)
                if repo_code:
                    cb['repository_code'] = repo_code

                # Service
                service_code = build_service_skeleton(entity_name, base_pkg)
                if service_code:
                    cb['service_code'] = service_code

                # Controller
                endpoint_path = f'/{domain_slug}' if domain_slug else f'/{_name_to_field_name(entity_name).lower()}'
                controller_code = build_controller_code(entity_name, base_pkg, endpoint_path)
                if controller_code:
                    cb['controller_code'] = controller_code

                code_blocks_by_task[tid] = cb

    # 11b. Guia por Task (COM codigo concreto + observacoes)
    task_guide = build_per_task_guide(tasks, project_sections, code_blocks_by_task)
    if task_guide:
        lines.append('## Guia por Task')
        lines.append('')
        lines.append(task_guide)
        lines.append('')

    # 12. Modelo de Dados (se campos extraidos dos requisitos)
    if req_fields:
        lines.append('## Modelo de Dados')
        lines.append('')
        # Agrupar campos por dominio: campos com "quantidade" ou "critério" sao da Aba 2 (Parâmetro Cota)
        # Os campos aparecem em ordem: primeiro Aba 1 (3 campos), depois Aba 2 (4 campos)
        # Identificar a transicao: campos repetidos (Balancete, Perfil) ou por nome
        cota_keywords = ['quantidade', 'critério', 'criterio', 'decimal', 'aproximação', 'aproximac']
        cota_fields = [f for f in req_fields if any(k in f['name'].lower() for k in cota_keywords)]
        # O restante forma a tabela de parametrizacao contabil (excluindo os que sao cota)
        geral_fields = [f for f in req_fields if f not in cota_fields]
        # Remover duplicatas de nome em geral_fields (manter primeira ocorrencia)
        seen_names = set()
        deduped = []
        for f in geral_fields:
            if f['name'].lower() not in seen_names:
                seen_names.add(f['name'].lower())
                deduped.append(f)
        geral_fields = deduped

        if cota_fields:
            lines.append(build_entity_field_table(cota_fields, 'ParametroCota (Entity)', 'PARAMETRO_COTA'))
            lines.append('')
            lines.append(build_dto_table(cota_fields, 'ParametroCotaInput / ParametroCotaOutput'))
            lines.append('')
            lines.append(build_migration_table(cota_fields, 'PARAMETRO_COTA', 'SEQ_PARAMETRO_COTA'))
            lines.append('')

        if geral_fields:
            lines.append(build_entity_field_table(geral_fields, 'ParametrizacaoContaContabil (Entity)', 'PARAMETRIZACAO_CONTA_CONTABIL'))
            lines.append('')
            lines.append(build_dto_table(geral_fields, 'ParametrizacaoContaContabilInput'))
            lines.append('')

    # 12b. Plano de Rollback
    rollback_section = build_rollback_section(tasks)
    if rollback_section:
        lines.append(rollback_section)
        lines.append('')

    # 13. Conteúdo para Jira
    if req_fields:
        jira_block = build_jira_block(ticket_id, summary, req_fields, tasks)
        if jira_block:
            lines.append(jira_block)
            lines.append('')

    # 14. Observações finais
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
