#!/usr/bin/env python3
"""Extrai dados ageis (sprint, story points, epic) de resposta API Agile Jira.

Uso: python3 jira_agile_parse.py < agile_response.json

Le: stdin com JSON de resposta da API Agile
Gera: stdout com JSON {sprint, storyPoints, epic}
"""

import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print('{"sprint": null, "storyPoints": null, "epic": null}')
        return

    fields = data.get('fields', {})
    print(json.dumps({
        'sprint': fields.get('sprint') or fields.get('customfield_10007'),
        'storyPoints': fields.get('storyPoints') or fields.get('customfield_10004'),
        'epic': fields.get('epic'),
    }))


if __name__ == '__main__':
    main()
