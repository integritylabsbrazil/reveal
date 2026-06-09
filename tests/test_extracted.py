"""Testes para scripts Python extraídos do bash."""

import json
import os
import sys
import unittest
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from jira_agile_parse import main as agile_parse
from jira_count_attachments import main as count_attachments


class TestJiraAgileParse(unittest.TestCase):
    def test_valid_response(self):
        stdin = json.dumps({'fields': {'sprint': {'id': 1}, 'storyPoints': 5, 'epic': 'EPIC-1'}})
        sys.stdin = StringIO(stdin)
        try:
            out = StringIO()
            old_out = sys.stdout
            sys.stdout = out
            agile_parse()
            sys.stdout = old_out
            result = json.loads(out.getvalue())
            self.assertEqual(result['sprint']['id'], 1)
            self.assertEqual(result['storyPoints'], 5)
            self.assertEqual(result['epic'], 'EPIC-1')
        finally:
            sys.stdin = sys.__stdin__

    def test_empty_response(self):
        stdin = ''
        sys.stdin = StringIO(stdin)
        try:
            out = StringIO()
            old_out = sys.stdout
            sys.stdout = out
            agile_parse()
            sys.stdout = old_out
            result = json.loads(out.getvalue())
            self.assertIsNone(result['sprint'])
        finally:
            sys.stdin = sys.__stdin__

    def test_no_fields(self):
        stdin = json.dumps({})
        sys.stdin = StringIO(stdin)
        try:
            out = StringIO()
            old_out = sys.stdout
            sys.stdout = out
            agile_parse()
            sys.stdout = old_out
            result = json.loads(out.getvalue())
            self.assertIsNone(result['sprint'])
        finally:
            sys.stdin = sys.__stdin__


class TestJiraCountAttachments(unittest.TestCase):
    def test_count_unique(self):
        data = [
            {'downloadedPath': '/tmp/a.pdf'},
            {'downloadedPath': '/tmp/b.pdf'},
            {'downloadedPath': '/tmp/a.pdf'},
        ]
        stdin = json.dumps(data)
        sys.stdin = StringIO(stdin)
        try:
            out = StringIO()
            old_out = sys.stdout
            sys.stdout = out
            count_attachments()
            sys.stdout = old_out
            self.assertEqual(int(out.getvalue().strip()), 2)
        finally:
            sys.stdin = sys.__stdin__

    def test_empty(self):
        stdin = '[]'
        sys.stdin = StringIO(stdin)
        try:
            out = StringIO()
            old_out = sys.stdout
            sys.stdout = out
            count_attachments()
            sys.stdout = old_out
            self.assertEqual(int(out.getvalue().strip()), 0)
        finally:
            sys.stdin = sys.__stdin__


if __name__ == '__main__':
    unittest.main()
