"""Testes para generate_tasks.py usando unittest (stdlib)."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from generate_tasks import (
    find_config, get_custom_field, get_change_keywords,
    detect_base_package, summarize_domain, java_tasks,
    LANGUAGE_HANDLERS
)

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def load(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


class TestFindConfig(unittest.TestCase):
    def test_not_found(self):
        self.assertIsNone(find_config('/tmp'))

    def test_found(self):
        cfg = find_config(os.path.join(FIXTURES, '..'))
        self.assertIsNotNone(cfg)
        self.assertTrue(cfg.endswith('.json'))


class TestCustomField(unittest.TestCase):
    def setUp(self):
        self.data = load('jira-data.json')

    def test_found(self):
        value = get_custom_field(self.data, 'Objetivo')
        self.assertIsInstance(value, str)
        self.assertGreater(len(value), 0)

    def test_not_found(self):
        value = get_custom_field(self.data, 'CampoInexistente')
        self.assertEqual(value, '')


class TestChangeKeywords(unittest.TestCase):
    def setUp(self):
        self.data = load('jira-data.json')

    def test_has_keys(self):
        kw = get_change_keywords(self.data)
        self.assertIn('needs_model', kw)
        self.assertIn('needs_api', kw)
        self.assertIn('needs_test', kw)


class TestDetectBasePackage(unittest.TestCase):
    def test_from_list(self):
        scan = {'packages': ['com.maps.dataa.tesouraria',
                              'com.maps.dataa.tesouraria.cota']}
        pkg = detect_base_package(scan)
        self.assertEqual(pkg, 'com.maps.dataa.tesouraria')

    def test_none(self):
        self.assertEqual(detect_base_package(None), 'com.exemplo.projeto')

    def test_empty(self):
        self.assertEqual(detect_base_package({'packages': []}),
                         'com.exemplo.projeto')

    def test_from_dict(self):
        scan = {'packages': {'com.maps.dataa': 10, 'com.maps': 20}}
        pkg = detect_base_package(scan)
        self.assertIn('com.maps', pkg)


class TestSummarizeDomain(unittest.TestCase):
    def test_from_summary(self):
        text = "Parametrização Cota Patrimonial - Criar parâmetro de casas decimais"
        domain = summarize_domain(text)
        self.assertTrue('Parametrização' in domain or 'Cota' in domain)

    def test_empty(self):
        self.assertEqual(summarize_domain(''), 'funcionalidade')

    def test_lowercase(self):
        domain = summarize_domain('criar um novo parametro de configuracao')
        self.assertNotEqual(domain, '')


class TestJavaTasks(unittest.TestCase):
    def setUp(self):
        self.config = load('refine-config.local.json')['projects'][0]
        self.scan = load('impact-report.json')
        self.jira = load('jira-data.json')
        self.kw = get_change_keywords(self.jira)
        self.tasks = java_tasks(self.config, self.scan, self.jira,
                                 self.kw, 'TEST-1')

    def test_generates_exact_count(self):
        # Com needs_calculation=True, gera 3 tasks (CRUD + processamento + demo)
        self.assertEqual(len(self.tasks), 3)

    def test_first_is_implementar(self):
        self.assertEqual(self.tasks[0]['tipo'], 'implementar')

    def test_first_is_junior(self):
        self.assertEqual(self.tasks[0]['nivel'], 'junior')

    def test_has_senior_for_calculation(self):
        levels = {t.get('nivel') for t in self.tasks}
        self.assertIn('senior', levels)

    def test_dependencies_are_valid(self):
        ids = {t['id'] for t in self.tasks}
        for t in self.tasks:
            for dep in t.get('dependeDe', []):
                self.assertIn(dep, ids,
                    f"Task {t['id']} depende de {dep} inexistente")

    def test_no_circular_dependencies(self):
        ids = {t['id'] for t in self.tasks}
        deps = {t['id']: t.get('dependeDe', []) for t in self.tasks}

        def has_cycle(node, visited, stack):
            visited.add(node)
            stack.add(node)
            for dep in deps.get(node, []):
                if dep not in ids:
                    continue
                if dep in stack:
                    return True
                if dep not in visited:
                    if has_cycle(dep, visited, stack):
                        return True
            stack.discard(node)
            return False

        visited = set()
        for t_id in ids:
            if t_id not in visited:
                self.assertFalse(has_cycle(t_id, visited, set()),
                    f"Ciclo na task {t_id}")

    def test_demo_has_artefatos(self):
        demo = [t for t in self.tasks if t['tipo'] == 'demo']
        self.assertEqual(len(demo), 1)
        self.assertIn('artefatos', demo[0])


class TestLanguageHandlers(unittest.TestCase):
    def test_java(self):
        self.assertIn('java', LANGUAGE_HANDLERS)

    def test_javascript(self):
        self.assertIn('javascript', LANGUAGE_HANDLERS)

    def test_typescript(self):
        self.assertIn('typescript', LANGUAGE_HANDLERS)


if __name__ == '__main__':
    unittest.main()
