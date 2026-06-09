#!/usr/bin/env python3
"""Conta anexos unicos baixados.

Uso: python3 jira_count_attachments.py < attachments.json

Le: stdin com array JSON de anexos (com campo downloadedPath)
Gera: stdout com o numero de anexos unicos
"""

import json
import sys


def main():
    data = json.load(sys.stdin)
    seen = set()
    for att in data:
        p = att.get('downloadedPath')
        if p:
            seen.add(p)
    print(len(seen))


if __name__ == '__main__':
    main()
