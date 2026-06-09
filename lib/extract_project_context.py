#!/usr/bin/env python3
"""Extrai contexto permanente de um projeto (padroes, arquitectura, convencoes).

Le arquivos-fonte reais e gera projects-context/<projeto>.md para reuso
entre tickets.

Uso: python3 extract_project_context.py --name NOME --path CAMINHO [--output DIR]
"""

import argparse
import os
import re
import sys
from datetime import datetime


def collect_java_files(project_path):
    """Percorre src/main/java e coleta arquivos .java."""
    src_main = os.path.join(project_path, 'src', 'main', 'java')
    if not os.path.isdir(src_main):
        src_main = os.path.join(project_path, 'src')
        if not os.path.isdir(src_main):
            return []
    java_files = []
    for root, dirs, files in os.walk(src_main):
        for f in files:
            if f.endswith('.java'):
                java_files.append(os.path.join(root, f))
    return java_files


def classify_file(filepath):
    """Classifica um arquivo Java pelo nome e conteudo."""
    basename = os.path.basename(filepath)
    name_lower = basename.lower()

    with open(filepath, 'r', errors='ignore') as f:
        content = f.read()

    # Indicadores por tipo
    is_controller = False
    is_service = False
    is_entity = False
    is_dto = False
    is_command = False
    is_repository = False

    if '@RestController' in content or '@Controller' in content:
        is_controller = True
    if re.search(r'@(Service|Component)\b', content):
        is_service = True
    if re.search(r'@(Entity|Table|Document)\b', content) or 'extends BaseEntity' in content or 'javax.persistence' in content:
        is_entity = True
    if ('DTO' in basename or 'Dto' in basename or 'dto' in basename or
        basename.endswith('Input.java') or basename.endswith('Output.java') or
        basename.endswith('Request.java') or basename.endswith('Response.java')):
        is_dto = True
    if ('Command' in basename or name_lower.endswith('command.java')) and '@Command' in content:
        is_command = True
    if 'Repository' in basename or name_lower.endswith('repository.java') or 'extends JpaRepository' in content:
        is_repository = True

    # Fallback: se tem muitos campos e getters/setters mas nao e entity, provavelmente DTO
    if not is_dto and not is_entity and not is_controller and not is_service:
        field_count = len(re.findall(r'\b(private|public)\s+\w+\s+\w+;', content))
        if field_count >= 3 and (re.search(r'@(Data|Getter|Setter|AllArgsConstructor|NoArgsConstructor)', content)):
            is_dto = True

    return {
        'controller': is_controller,
        'service': is_service,
        'entity': is_entity,
        'dto': is_dto,
        'command': is_command,
        'repository': is_repository,
    }


def extract_annotations(content):
    """Extrai anotacoes de classe e metodo de um arquivo Java."""
    all_annotations = set()
    # Capturar bloco de anotacoes antes da declaracao de classe
    m = re.search(r'((?:@\w+(?:\([^)]*\))?\s*\n)+)\s*(public\s+)?(class|interface|enum)\s+', content, re.MULTILINE)
    if m:
        block = m.group(1)
        for a in re.finditer(r'@(\w+(?:\([^)]*\))?)', block):
            all_annotations.add(a.group(1))
    method_annotations = set()
    for m in re.finditer(r'(@\w+(?:\([^)]*\))?)\s*\n\s*(public|private|protected)\s+\w+\s+\w+\s*\(', content, re.MULTILINE):
        method_annotations.add(m.group(1).split('(')[0])
    return sorted(all_annotations), sorted(method_annotations)


def extract_package(content):
    m = re.search(r'^package\s+([\w.]+);', content, re.MULTILINE)
    return m.group(1) if m else ''


def extract_imports(content):
    return re.findall(r'^import\s+([\w.*]+);', content, re.MULTILINE)


def read_file_safe(filepath):
    try:
        with open(filepath, 'r', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''


def build_directory_tree(project_path, max_depth=4):
    """Gera arvore de diretorios da src indentada."""
    src_main = os.path.join(project_path, 'src', 'main', 'java')
    if not os.path.isdir(src_main):
        return ''
    lines = []
    base_len = len(src_main.rstrip('/')) + 1

    for root, dirs, files in os.walk(src_main):
        depth = root[base_len:].count(os.sep)
        if depth > max_depth:
            continue
        if depth == 0:
            indent = ''
        else:
            indent = '  ' * depth
        dirname = os.path.basename(root) if depth > 0 else os.path.basename(root)
        if dirname == '__pycache__':
            continue
        lines.append(f'{indent}{dirname}/')
        # So mostrar arquivos no nivel maximo
        if depth == max_depth:
            for f in sorted(files)[:3]:
                if f.endswith('.java'):
                    lines.append(f'{indent}  {f}')

    return '\n'.join(lines[:60])


def extract_patterns(java_files, project_path):
    """Analisa todos os arquivos e extrai padroes."""
    controllers = []
    services = []
    entities = []
    dtos = []
    commands = []
    repositories = []

    # Para extrair anotacoes unicas
    all_controller_annotations = set()
    all_controller_method_annotations = set()
    all_service_annotations = set()
    all_entity_annotations = set()
    all_dto_annotations = set()
    all_command_annotations = set()
    all_repository_annotations = set()
    base_packages = set()
    all_endpoints = set()

    for filepath in java_files:
        content = read_file_safe(filepath)
        if not content:
            continue
        cls = classify_file(filepath)
        pkg = extract_package(content)
        if pkg:
            base_packages.add(pkg)
        annotations, method_annotations = extract_annotations(content)
        relpath = os.path.relpath(filepath, project_path)
        basename = os.path.basename(filepath)

        if cls['controller']:
            controllers.append((pkg, basename, relpath, annotations, method_annotations, content))
            all_controller_annotations.update(annotations)
            all_controller_method_annotations.update(method_annotations)
            # Extrair endpoints
            for m in re.finditer(r'@(\w+Mapping)\(["\']([^"\']+)["\']', content):
                all_endpoints.add((m.group(1), m.group(2)))
            for m in re.finditer(r'@RequestMapping\(["\']([^"\']+)["\']', content):
                all_endpoints.add(('@RequestMapping', m.group(1)))

        if cls['service']:
            services.append((pkg, basename, relpath, annotations, method_annotations, content))
            all_service_annotations.update(annotations)

        if cls['entity']:
            entities.append((pkg, basename, relpath, annotations, method_annotations, content))
            all_entity_annotations.update(annotations)

        if cls['dto']:
            dtos.append((pkg, basename, relpath, annotations, method_annotations, content))
            all_dto_annotations.update(annotations)

        if cls['command']:
            commands.append((pkg, basename, relpath, annotations, method_annotations, content))
            all_command_annotations.update(annotations)

        if cls['repository']:
            repositories.append((pkg, basename, relpath, annotations, method_annotations, content))
            all_repository_annotations.update(annotations)

    # Determinar pacote base pelo prefixo comum
    base_pkg = ''
    if base_packages:
        pkgs = sorted(base_packages)
        common = os.path.commonprefix([p.replace('.', '/') for p in pkgs])
        base_pkg = common.replace('/', '.')
        # Pegar ate 4 segmentos
        parts = base_pkg.split('.')
        if len(parts) > 4:
            base_pkg = '.'.join(parts[:4])

    return {
        'base_pkg': base_pkg,
        'controllers': controllers[:5],
        'services': services[:5],
        'entities': entities[:3],
        'dtos': dtos[:5],
        'commands': commands[:3],
        'repositories': repositories[:3],
        'controller_annotations': all_controller_annotations,
        'controller_method_annotations': all_controller_method_annotations,
        'service_annotations': all_service_annotations,
        'entity_annotations': all_entity_annotations,
        'dto_annotations': all_dto_annotations,
        'command_annotations': all_command_annotations,
        'repository_annotations': all_repository_annotations,
        'endpoints': all_endpoints,
    }


def format_annotations(annotations):
    return '\n'.join(f'- `{a}`' for a in sorted(annotations) if a.strip('@'))


def generate_markdown(name, project_path, patterns, config_data):
    lines = []
    lines.append(f'# Contexto do Projeto — {name}')
    lines.append('')
    lines.append(f'Gerado automaticamente em {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('')
    lines.append('---')
    lines.append('')

    # 1. Stack
    lines.append('## Stack')
    lines.append('')
    lines.append('| Tecnologia | Versao |')
    lines.append('|------------|--------|')
    lang = config_data.get('language', 'java').capitalize()
    build = config_data.get('buildTool', 'Pendente')
    lines.append(f'| Linguagem | {lang} |')
    lines.append(f'| Build | {build} |')
    lines.append('')
    lines.append('> Consulte o `AGENTS.md` do projeto para versoes exatas (Spring Boot, Java, etc.).')
    lines.append('')

    # 2. Arquitetura (tentar do projectDocs)
    lines.append('## Arquitetura')
    lines.append('')
    lines.append('Package-by-Feature com padrao de modularizacao por funcionalidade.')
    lines.append('Cada feature contem seus proprios controller, service, domain, repository.')
    lines.append('')
    lines.append('> Consulte o `AGENTS.md` do projeto para detalhes arquiteturais especificos.')
    lines.append('')

    # 3. Pacote Base
    if patterns['base_pkg']:
        lines.append('## Pacote Base')
        lines.append('')
        lines.append(f'`{patterns["base_pkg"]}`')
        lines.append('')

    # 4. Estrutura de Diretorios
    tree = build_directory_tree(project_path)
    if tree:
        lines.append('## Estrutura de Diretorios')
        lines.append('')
        lines.append('```')
        lines.append(tree)
        lines.append('```')
        lines.append('')

    # 5. Controllers
    if patterns['controllers']:
        lines.append('## Padroes de Controllers')
        lines.append('')
        lines.append('### Anotacoes de Classe')
        lines.append('')
        lines.append(format_annotations(patterns['controller_annotations']))
        lines.append('')
        lines.append('### Anotacoes de Metodo')
        lines.append('')
        lines.append(format_annotations(patterns['controller_method_annotations']))
        lines.append('')
        if patterns['endpoints']:
            lines.append('### Endpoints Encontrados')
            lines.append('')
            lines.append('| Anotacao | Path |')
            lines.append('|----------|------|')
            for ann, path in sorted(patterns['endpoints']):
                lines.append(f'| {ann} | {path} |')
            lines.append('')
        lines.append('### Exemplos')
        lines.append('')
        for pkg, bname, relpath, anns, meth_anns, content in patterns['controllers']:
            lines.append(f'- `{pkg}.{bname.replace(".java","")}`  — `{relpath}`')
        lines.append('')

    # 6. Services
    if patterns['services']:
        lines.append('## Padroes de Services')
        lines.append('')
        lines.append('### Anotacoes')
        lines.append('')
        lines.append(format_annotations(patterns['service_annotations']))
        lines.append('')
        lines.append('### Exemplos')
        lines.append('')
        for pkg, bname, relpath, anns, meth_anns, content in patterns['services']:
            lines.append(f'- `{pkg}.{bname.replace(".java","")}`  — `{relpath}`')
        lines.append('')

    # 7. Entities
    if patterns['entities']:
        lines.append('## Padroes de Entities')
        lines.append('')
        lines.append('### Anotacoes')
        lines.append('')
        lines.append(format_annotations(patterns['entity_annotations']))
        lines.append('')
        lines.append('### Exemplos')
        lines.append('')
        for pkg, bname, relpath, anns, meth_anns, content in patterns['entities']:
            lines.append(f'- `{pkg}.{bname.replace(".java","")}`  — `{relpath}`')
        lines.append('')

    # 8. DTOs
    if patterns['dtos']:
        lines.append('## Padroes de DTOs')
        lines.append('')
        lines.append('### Anotacoes')
        lines.append('')
        lines.append(format_annotations(patterns['dto_annotations']))
        lines.append('')
        lines.append('### Exemplos')
        lines.append('')
        for pkg, bname, relpath, anns, meth_anns, content in patterns['dtos']:
            lines.append(f'- `{pkg}.{bname.replace(".java","")}`  — `{relpath}`')
        lines.append('')

    # 9. Repositories
    if patterns['repositories']:
        lines.append('## Padroes de Repositories')
        lines.append('')
        lines.append('### Anotacoes')
        lines.append('')
        lines.append(format_annotations(patterns['repository_annotations']))
        lines.append('')
        lines.append('### Exemplos')
        lines.append('')
        for pkg, bname, relpath, anns, meth_anns, content in patterns['repositories']:
            lines.append(f'- `{pkg}.{bname.replace(".java","")}`  — `{relpath}`')
        lines.append('')

    # 10. Resumo de Pacotes
    lines.append('## Pacotes Encontrados')
    lines.append('')
    lines.append('```')
    pkg_count = len(set(p[0] for p in (patterns['controllers'] + patterns['services'] +
                                        patterns['entities'] + patterns['dtos'] +
                                        patterns['commands'] + patterns['repositories'])))
    lines.append(f'Total de classes analisadas: ~{pkg_count} pacotes')
    base = patterns['base_pkg']
    if base:
        # Mostrar subpacotes de primeiro nivel
        subs = set()
        for pkg, _, _, _, _, _ in (patterns['controllers'] + patterns['services'] +
                                    patterns['entities'] + patterns['dtos'] +
                                    patterns['commands'] + patterns['repositories']):
            if pkg.startswith(base):
                rest = pkg[len(base)+1:]
                first = rest.split('.')[0] if rest else ''
                if first:
                    subs.add(f'{base}.{first}')
        for s in sorted(subs):
            lines.append(f'- {s}')
    lines.append('```')
    lines.append('')

    lines.append('---')
    lines.append('')
    lines.append(f'*Contexto gerado em {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')
    lines.append('*Regenerar com: `./generate-project-context.sh {name}`*')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Extrai contexto de projeto para reuso entre tickets')
    parser.add_argument('--name', required=True, help='Nome do projeto')
    parser.add_argument('--path', required=True, help='Caminho do projeto')
    parser.add_argument('--output', default='', help='Diretorio de saida (default: projects-context/ ao lado do script)')
    parser.add_argument('--language', default='java', help='Linguagem do projeto')
    parser.add_argument('--build-tool', default='', help='Ferramenta de build')
    args = parser.parse_args()

    project_path = os.path.abspath(args.path)
    if not os.path.isdir(project_path):
        print(f"[CTX] ERRO: {project_path} nao encontrado", file=sys.stderr)
        sys.exit(1)

    # Output dir
    if args.output:
        out_dir = args.output
    else:
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'projects-context')
    os.makedirs(out_dir, exist_ok=True)

    print(f"[CTX] Analisando {project_path}...", file=sys.stderr)
    java_files = collect_java_files(project_path)
    print(f"[CTX] Encontrados {len(java_files)} arquivos .java", file=sys.stderr)

    if not java_files:
        print(f"[CTX] AVISO: Nenhum arquivo .java encontrado em {project_path}", file=sys.stderr)

    patterns = extract_patterns(java_files, project_path)

    config_data = {
        'language': args.language,
        'buildTool': args.build_tool or 'Pendente',
    }

    md = generate_markdown(args.name, project_path, patterns, config_data)

    out_file = os.path.join(out_dir, f'{args.name}.md')
    with open(out_file, 'w') as f:
        f.write(md)

    print(f"[CTX] Contexto salvo em {out_file}", file=sys.stderr)
    print(f"[CTX] {len(patterns['controllers'])} controllers, {len(patterns['services'])} services, {len(patterns['entities'])} entities, {len(patterns['dtos'])} DTOs", file=sys.stderr)


if __name__ == '__main__':
    main()
