#!/usr/bin/env python3
"""Renderizador simples de templates Mustache-like.

Uso: python3 render_template.py TEMPLATE_FILE KEY1=VAL1 KEY2=VAL2 ...

Substitui {{KEY}} no template pelo valor correspondente.
Valores podem ser passados como:
  - Argumentos CLI: KEY=VAL
  - Variaveis de ambiente: export KEY=VAL
  - Arquivo JSON: --json FILE (cada chave no JSON vira variavel)

Valores que contem \n serao convertidos para quebras de linha reais.
"""

import json
import os
import re
import sys


def parse_value(val):
    """Converte \\n literal para quebras de linha reais."""
    return val.replace('\\n', '\n').replace('\\t', '\t')


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    template_file = args[0]
    if not os.path.exists(template_file):
        print(f"ERRO: Template {template_file} nao encontrado", file=sys.stderr)
        sys.exit(1)

    with open(template_file) as f:
        template = f.read()

    # Coletar variaveis
    variables = {}

    # 1. Variaveis de ambiente (menor prioridade)
    for k, v in os.environ.items():
        if k.startswith('TEMPLATE_'):
            variables[k[9:]] = v

    # 2. Argumentos CLI
    for arg in args[1:]:
        if arg.startswith('--json='):
            json_file = arg[7:]
            if os.path.exists(json_file):
                with open(json_file) as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if isinstance(v, (str, int, float, bool)):
                            variables[k] = str(v)
        elif arg.startswith('--json_file='):
            pass  # already handled above
        elif '=' in arg:
            key, value = arg.split('=', 1)
            variables[key] = parse_value(value)

    # 3. Ler variaveis de arquivo JSON padrao (template_name.vars.json)
    vars_file = template_file.rsplit('.', 1)[0] + '.vars.json'
    if os.path.exists(vars_file):
        with open(vars_file) as f:
            data = json.load(f)
            for k, v in data.items():
                if isinstance(v, (str, int, float, bool)):
                    variables[k] = str(v)

    # Substituir {{VARIAVEIS}}
    def replace_var(match):
        key = match.group(1).strip()
        if key in variables:
            return variables[key]
        # Deixar intacto se variavel nao existe
        return match.group(0)

    result = re.sub(r'\{\{(\w+)\}\}', replace_var, template)

    # Substituir blocos condicionais: {% if KEY %}...{% endif %}
    def replace_if(match):
        inner = match.group(1)
        # Extrair condicao
        cond_match = re.match(r'if\s+(\w+)\s*(.*)', inner)
        if not cond_match:
            return match.group(0)
        cond_key = cond_match.group(1)
        rest = cond_match.group(2)
        # Extrair conteudo (tudo apos a condicao ate endif)
        content_match = re.search(r'([\s\S]*)', rest)
        content = content_match.group(1) if content_match else rest

        # Verificar se a condicao eh verdadeira (variavel existe e nao vazia)
        if cond_key in variables and variables[cond_key] and variables[cond_key] not in ('', 'null', 'None'):
            return content
        return ''

    result = re.sub(r'\{%\s*(if\s+\w+[\s\S]*?)\s*%\}', replace_if, result)

    # Remover blocos condicionais que nao foram processados
    result = re.sub(r'\{% if.*?%\}.*?\{% endif %\}', '', result, flags=re.DOTALL)

    print(result, end='')


if __name__ == '__main__':
    main()
