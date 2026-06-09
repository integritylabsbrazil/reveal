#!/usr/bin/env python3
"""
humanize_text.py — Transforma markdown estruturado em texto de aparencia
mais natural, removendo marcadores de template e ajustando formatacao.

Uso: cat input.md | python3 humanize_text.py [--jira|--pr]

  --jira  (padrao) Preserva headings e blocos de codigo (build_adf.py os
                   converte para ADF). Remove ---, ***, ___, backticks
                   inline e colapsa linhas em branco multiplas.

  --pr             Converte #/##/### para **texto** (negrito) pois PR comments
                   sao markdown puro, sem conversao ADF.
                   Remove blocos de codigo e backticks inline.
                   Converte tabelas 2-3 colunas para bullet lists.
"""

import re
import sys


def remove_separators(line):
    stripped = line.strip()
    if re.match(r'^[-*_]{3,}\s*$', stripped):
        return ''
    return line


def remove_inline_backticks(text):
    """Remove backticks around inline code: `text` → text"""
    return re.sub(r'`([^`]+)`', r'\1', text)


def is_fence_line(stripped):
    return stripped.startswith('```') or stripped.startswith('~~~')


def collapse_blank_lines(lines):
    result = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return result


def convert_headings_to_bold(line):
    stripped = line.strip()
    m = re.match(r'^(#{1,3})\s+(.+)$', stripped)
    if m:
        indent = line[:len(line) - len(line.lstrip())]
        text = m.group(2)
        return f'{indent}**{text}**'
    return line


def is_small_table(lines, start_idx):
    count = 0
    for i in range(start_idx, min(start_idx + 20, len(lines))):
        stripped = lines[i].strip()
        if not stripped.startswith('|') or not stripped.endswith('|'):
            break
        if is_separator_row(stripped):
            continue
        count += 1
        if count > 2:
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if len(cells) > 3:
                return False
    return True


def is_separator_row(stripped):
    cells = stripped.split('|')[1:-1]
    return all(re.match(r'^[-:\s]+$', c.strip()) for c in cells) if cells else False


def convert_table_to_list(lines, start_idx):
    result = []
    header_saved = None
    for i in range(start_idx, len(lines)):
        stripped = lines[i].strip()
        if not stripped.startswith('|') or not stripped.endswith('|'):
            break
        if is_separator_row(stripped):
            continue
        cells = [c.strip() for c in stripped.split('|')[1:-1]]
        if header_saved is None:
            header_saved = cells
        else:
            if len(cells) == 2 and len(header_saved) >= 2:
                result.append(f'  - **{cells[0]}**: {cells[1]}')
            elif len(cells) == 3 and len(header_saved) >= 3:
                result.append(f'  - **{cells[0]}**: {cells[1]} ({cells[2]})')
            else:
                result.append('  - ' + ' — '.join(cells))
    return result, start_idx + len(result) + 1 if result else start_idx + 1


def humanize(text, mode='jira'):
    lines = text.split('\n')
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == '':
            result.append('')
            i += 1
            continue

        # Remove separators
        cleaned = remove_separators(line)
        if cleaned == '':
            result.append('')
            i += 1
            continue

        # PR mode: skip fenced code blocks (nao renderizam bem em comments)
        if mode == 'pr' and is_fence_line(stripped):
            i += 1
            while i < len(lines) and not is_fence_line(lines[i].strip()):
                i += 1
            i += 1  # skip closing fence
            continue

        if mode == 'pr':
            if re.match(r'^\|.*\|$', stripped) and not re.match(r'^\|[-:\s]+\|$', stripped):
                if is_small_table(lines, i):
                    items, next_i = convert_table_to_list(lines, i)
                    result.extend(items)
                    i = next_i
                    continue

            result.append(convert_headings_to_bold(remove_inline_backticks(cleaned)))
        else:
            # Jira mode: preserve code blocks, just remove inline backticks
            result.append(remove_inline_backticks(cleaned))

        i += 1

    result = collapse_blank_lines(result)

    # Ensure trailing newline
    output = '\n'.join(result)
    if output and not output.endswith('\n'):
        output += '\n'
    return output


def main():
    mode = 'jira'
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    flags = [a for a in sys.argv[1:] if a.startswith('-')]

    if '--pr' in flags:
        mode = 'pr'
    if '--jira' in flags:
        mode = 'jira'

    text = sys.stdin.read()
    result = humanize(text, mode=mode)
    sys.stdout.write(result)


if __name__ == '__main__':
    main()
