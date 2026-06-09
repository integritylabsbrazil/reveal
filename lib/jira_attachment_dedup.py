#!/usr/bin/env python3
"""Deduplica anexos Jira por MD5 e faz download.

Uso: python3 jira_attachment_dedup.py ATTACH_DIR < attachments.json

Le: stdin com array JSON de anexos (contentUrl, filename)
Gera: stdout com array JSON enriquecido (downloadedPath, md5)
"""

import hashlib
import json
import os
import subprocess
import sys


def main():
    data = json.load(sys.stdin)
    if not data:
        print(json.dumps(data))
        return

    attach_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(attach_dir, exist_ok=True)

    seen_md5 = {}
    result = []

    for att in data:
        entry = dict(att)
        content_url = att.get('contentUrl', '')
        filename = att.get('filename', 'unknown')

        if not content_url:
            entry['downloadedPath'] = None
            entry['downloadError'] = 'no contentUrl'
            result.append(entry)
            continue

        tmp = os.path.join(attach_dir, '.tmp_' + filename)
        try:
            env = os.environ.copy()
            user = env.get('JIRA_USER', '')
            token = env.get('JIRA_TOKEN', '')
            subprocess.run(
                ['curl', '-sL', '-o', tmp, '-u', f'{user}:{token}', content_url],
                check=True, capture_output=True, timeout=30
            )
        except Exception as e:
            entry['downloadedPath'] = None
            entry['downloadError'] = str(e)
            result.append(entry)
            continue

        md5 = hashlib.md5()
        with open(tmp, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                md5.update(chunk)
        md5_hex = md5.hexdigest()

        if md5_hex in seen_md5:
            os.remove(tmp)
            entry['downloadedPath'] = seen_md5[md5_hex]
            entry['md5'] = md5_hex
            result.append(entry)
            continue

        final_path = os.path.join(attach_dir, filename)
        counter = 1
        while os.path.exists(final_path):
            name, ext = os.path.splitext(filename)
            final_path = os.path.join(attach_dir, f'{name}_{counter}{ext}')
            counter += 1

        os.rename(tmp, final_path)
        seen_md5[md5_hex] = final_path
        entry['downloadedPath'] = final_path
        entry['md5'] = md5_hex
        result.append(entry)

    print(json.dumps(result))


if __name__ == '__main__':
    main()
