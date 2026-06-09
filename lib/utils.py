#!/usr/bin/env python3
"""Shared utility functions for reveal tooling."""

import json
import os


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


def get_custom_field(jira_data, name, prefer_rendered=True):
    for v in jira_data.get('customFields', {}).values():
        if isinstance(v, dict) and v.get('name') == name:
            if prefer_rendered:
                rendered = v.get('rendered')
                if rendered and isinstance(rendered, str) and rendered.strip():
                    return rendered
            val = v.get('value')
            if val and isinstance(val, str):
                return val
            if isinstance(val, (list, dict)):
                return str(val)
            return ''
    return ''


def detect_base_package(scan_data):
    if not scan_data:
        return 'com.exemplo.projeto'
    packages = scan_data.get('packages', [])
    if not packages:
        return 'com.exemplo.projeto'
    if isinstance(packages, list):
        longest = max(packages, key=len) if packages else 'com.exemplo'
        parts = longest.split('.')
        if len(parts) >= 4:
            return '.'.join(parts[:4])
        return '.'.join(parts[:3]) if len(parts) >= 3 else longest
    if isinstance(packages, dict):
        sorted_pkgs = sorted(packages.items(), key=lambda x: -x[1])
        if sorted_pkgs:
            top = sorted_pkgs[0][0]
            parts = top.split('.')
            if len(parts) >= 4:
                return '.'.join(parts[:4])
            return '.'.join(parts[:3]) if len(parts) >= 3 else top
    return 'com.exemplo.projeto'


def validate_status_tasks(data):
    errors = []
    if not isinstance(data, dict):
        return ['status-tasks.json: root must be an object']
    if 'ticketId' not in data:
        errors.append('status-tasks.json: missing "ticketId"')
    if 'tarefas' not in data or not isinstance(data.get('tarefas'), list):
        errors.append('status-tasks.json: missing or invalid "tarefas" (must be array)')
    else:
        for i, t in enumerate(data['tarefas']):
            for field in ('id', 'projeto', 'descricao', 'status', 'tipo'):
                if field not in t:
                    errors.append(f'status-tasks.json: tarefa[{i}] missing "{field}"')
    return errors


def validate_impact_report(data):
    errors = []
    if not isinstance(data, dict):
        return ['impact-report.json: root must be an object']
    return errors


def validate_jira_data(data):
    errors = []
    if not isinstance(data, dict):
        return ['jira-data.json: root must be an object']
    if 'ticketId' not in data:
        errors.append('jira-data.json: missing "ticketId"')
    if 'basic' not in data or not isinstance(data.get('basic'), dict):
        errors.append('jira-data.json: missing or invalid "basic" object')
    return errors


def validate_file(path, schema_name='status_tasks'):
    data = load_json(path)
    if data is None:
        return [f'{path}: file not found or invalid JSON']
    if schema_name == 'status_tasks':
        return validate_status_tasks(data)
    elif schema_name == 'impact_report':
        return validate_impact_report(data)
    elif schema_name == 'jira_data':
        return validate_jira_data(data)
    return [f'Unknown schema: {schema_name}']
