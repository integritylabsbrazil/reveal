#!/usr/bin/env python3
"""
build_adf.py — Conversor markdown -> ADF (Atlassian Document Format).
Le JSON com campo 'observacoes' via stdin, imprime JSON ADF via stdout.

Input:  {"observacoes": "# Titulo\\n\\n```java\\ncode\\n```\\n| a | b |"}
Output: {"type":"doc","version":1,"content":[...]}

Regras de conversao:
  # Texto      -> heading level 2
  ## Texto     -> heading level 3
  ```lang ... -> codeBlock (language = lang)
  | cel | cel | -> table (linhas consecutivas agrupadas)
  --- (separadores de tabela) -> ignorado
  demais linhas -> paragraph

Nao faz parsing de secoes nomeadas, nem tabela de metadados.
"""

import json
import re
import sys


def bold(text):
    return {'type': 'text', 'text': text, 'marks': [{'type': 'strong'}]}


def plain(text):
    return {'type': 'text', 'text': text}


def paragraph(content):
    if not isinstance(content, list):
        content = [content]
    return {'type': 'paragraph', 'content': content}


def heading(level, text):
    return {
        'type': 'heading',
        'attrs': {'level': level},
        'content': [bold(text)]
    }


def code_block(text, language='java'):
    return {
        'type': 'codeBlock',
        'attrs': {'language': language},
        'content': [{'type': 'text', 'text': text}]
    }


def make_table(rows):
    content = []
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.split('|')[1:-1]]
        cell_type = 'tableHeader' if i == 0 else 'tableCell'
        content.append({
            'type': 'tableRow',
            'content': [{
                'type': cell_type,
                'content': [paragraph(plain(c))]
            } for c in cells]
        })
    return {'type': 'table', 'attrs': {'layout': 'default'}, 'content': content}


def is_table_separator(line):
    """Check if a line is a markdown table separator: |---|---| etc."""
    stripped = line.strip()
    if not (stripped.startswith('|') and stripped.endswith('|')):
        return False
    cells = [c.strip() for c in stripped.split('|')[1:-1]]
    return all(re.match(r'^[-:\s]+$', c) for c in cells if c)


def is_table_row(line):
    stripped = line.strip()
    return stripped.startswith('|') and stripped.endswith('|')


def build(md_text):
    doc = {'type': 'doc', 'version': 1, 'content': []}
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            i += 1
            continue

        # Heading level 1 -> ADF heading level 2
        if stripped.startswith('# ') and not stripped.startswith('## '):
            doc['content'].append(heading(2, stripped[2:]))
            i += 1
            continue

        # Heading level 2 -> ADF heading level 3
        if stripped.startswith('## '):
            doc['content'].append(heading(3, stripped[3:]))
            i += 1
            continue

        # Code block
        if stripped.startswith('```'):
            lang = stripped.strip('`').strip() or 'java'
            code_lines = []
            i += 1
            while i < len(lines):
                if lines[i].strip().startswith('```'):
                    i += 1
                    break
                code_lines.append(lines[i])
                i += 1
            doc['content'].append(code_block('\n'.join(code_lines), lang))
            continue

        # Table (consecutive rows, skipping separator)
        if is_table_row(stripped) and not is_table_separator(stripped):
            table_rows = [stripped]
            i += 1
            # Skip separator line if present
            if i < len(lines) and is_table_separator(lines[i].strip()):
                i += 1
            # Collect remaining rows
            while i < len(lines):
                row = lines[i].strip()
                if is_table_row(row) and not is_table_separator(row):
                    table_rows.append(row)
                    i += 1
                else:
                    break
            doc['content'].append(make_table(table_rows))
            continue

        # Regular paragraph
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith('#') or nxt.startswith('```') or is_table_row(nxt):
                break
            para_lines.append(nxt)
            i += 1
        doc['content'].append(paragraph(plain('\n'.join(para_lines))))

    return doc


if __name__ == '__main__':
    raw = sys.stdin.read()
    try:
        params = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)

    md_text = params.get('observacoes', '')
    doc = build(md_text)
    print(json.dumps(doc))
