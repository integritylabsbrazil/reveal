"""Testes para lib/utils.py usando unittest (stdlib)."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from utils import load_json, get_custom_field, detect_base_package, validate_status_tasks, validate_impact_report, validate_jira_data


class TestLoadJson(unittest.TestCase):
    def test_file_not_found(self):
        self.assertIsNone(load_json('/tmp/nonexistent_file_12345.json'))

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            fpath = f.name
        try:
            self.assertIsNone(load_json(fpath))
        finally:
            os.unlink(fpath)

    def test_valid_json(self):
        data = {'key': 'value'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            fpath = f.name
        try:
            result = load_json(fpath)
            self.assertEqual(result, data)
        finally:
            os.unlink(fpath)

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not json')
            fpath = f.name
        try:
            self.assertIsNone(load_json(fpath))
        finally:
            os.unlink(fpath)


class TestGetCustomField(unittest.TestCase):
    def test_found(self):
        data = {'customFields': {'cf1': {'name': 'Target', 'value': 'val'}}}
        self.assertEqual(get_custom_field(data, 'Target'), 'val')

    def test_not_found(self):
        data = {'customFields': {}}
        self.assertEqual(get_custom_field(data, 'Missing'), '')

    def test_empty_data(self):
        self.assertEqual(get_custom_field({}, 'X'), '')


class TestDetectBasePackage(unittest.TestCase):
    def test_from_list(self):
        data = {'packages': ['com.maps.dataa.tesouraria']}
        self.assertEqual(detect_base_package(data), 'com.maps.dataa.tesouraria')

    def test_from_dict(self):
        data = {'packages': {'com.maps.dataa': 10, 'com.other': 5}}
        self.assertEqual(detect_base_package(data), 'com.maps.dataa')

    def test_empty(self):
        self.assertEqual(detect_base_package(None), 'com.exemplo.projeto')
        self.assertEqual(detect_base_package({'packages': []}), 'com.exemplo.projeto')


class TestValidateStatusTasks(unittest.TestCase):
    def test_valid(self):
        data = {
            'ticketId': 'PROJ-123',
            'tarefas': [{'id': '0001', 'projeto': 'x', 'descricao': 'd', 'status': 'pendente', 'tipo': 'implementar'}]
        }
        self.assertEqual(validate_status_tasks(data), [])

    def test_missing_ticket_id(self):
        data = {'tarefas': []}
        errors = validate_status_tasks(data)
        self.assertIn('ticketId', errors[0])

    def test_missing_tarefas(self):
        errors = validate_status_tasks({})
        self.assertTrue(any('tarefas' in e for e in errors))

    def test_tarefa_missing_field(self):
        data = {
            'ticketId': 'P-1',
            'tarefas': [{'id': '0001'}]  # missing projeto, descricao, status, tipo
        }
        errors = validate_status_tasks(data)
        self.assertTrue(any('projeto' in e for e in errors))
        self.assertTrue(any('descricao' in e for e in errors))

    def test_not_dict(self):
        self.assertEqual(len(validate_status_tasks([])), 1)


class TestValidateImpactReport(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_impact_report({}), [])

    def test_not_dict(self):
        self.assertEqual(len(validate_impact_report('str')), 1)


class TestValidateJiraData(unittest.TestCase):
    def test_valid(self):
        data = {'ticketId': 'P-1', 'basic': {}}
        self.assertEqual(validate_jira_data(data), [])

    def test_missing_ticket_id(self):
        errors = validate_jira_data({'basic': {}})
        self.assertTrue(any('ticketId' in e for e in errors))

    def test_missing_basic(self):
        errors = validate_jira_data({'ticketId': 'P-1'})
        self.assertTrue(any('basic' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
