#!/usr/bin/env python3
"""Monta JSON completo do Jira a partir de arquivos temporarios."""

import json
import os
import sys
from datetime import datetime, timezone


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


def main():
    if len(sys.argv) < 3:
        print("Uso: assemble_jira.py TICKET_ID TMP_DIR", file=sys.stderr)
        sys.exit(1)

    ticket_id = sys.argv[1]
    tmp_dir = sys.argv[2]

    basic = load_json(os.path.join(tmp_dir, "basic.json"), {})
    epic = load_json(os.path.join(tmp_dir, "epic.json"), None)
    linked = load_json(os.path.join(tmp_dir, "linked.json"), [])
    subtasks = load_json(os.path.join(tmp_dir, "subtasks.json"), [])
    comments = load_json(os.path.join(tmp_dir, "comments.json"), [])
    changelog = load_json(os.path.join(tmp_dir, "changelog.json"), [])
    attachments = load_json(os.path.join(tmp_dir, "attachments.json"), [])
    agile = load_json(os.path.join(tmp_dir, "agile.json"), {})

    fields = basic.get("fields", {})
    rendered = basic.get("renderedFields", {})
    names = basic.get("names", {})
    schema = basic.get("schema", {})

    # Extrair todos os campos personalizados (customfield_*)
    custom_fields = {}
    for field_id, display_name in names.items():
        if field_id.startswith("customfield_"):
            raw_value = fields.get(field_id)
            rendered_value = rendered.get(field_id)
            field_schema = schema.get(field_id, {})

            # Pular campos vazios
            if raw_value is None or raw_value == "" or raw_value == [] or raw_value == {}:
                continue

            # Extrair texto de campos ADF (Atlassian Document Format)
            if isinstance(raw_value, dict) and raw_value.get("type") == "doc":
                texts = []

                def extract_text(node):
                    if isinstance(node, dict):
                        if node.get("type") == "text" and node.get("text"):
                            texts.append(node["text"])
                        for v in node.values():
                            extract_text(v)
                    elif isinstance(node, list):
                        for item in node:
                            extract_text(item)

                extract_text(raw_value)
                display_value = "\n".join(texts) if texts else str(raw_value)[:200]
                custom_fields[field_id] = {
                    "id": field_id,
                    "name": display_name,
                    "value": display_value,
                    "rendered": rendered_value,
                    "type": "text",
                }
                continue

            # Formatar valor para exibicao
            if isinstance(raw_value, dict) and "value" in raw_value:
                display_value = raw_value["value"]
            elif isinstance(raw_value, dict) and "name" in raw_value:
                display_value = raw_value["name"]
            elif isinstance(raw_value, dict) and "displayName" in raw_value:
                display_value = raw_value["displayName"]
            elif isinstance(raw_value, list):
                vals = []
                for item in raw_value:
                    if isinstance(item, dict) and "value" in item:
                        vals.append(item["value"])
                    elif isinstance(item, dict) and "name" in item:
                        vals.append(item["name"])
                    elif isinstance(item, dict) and "displayName" in item:
                        vals.append(item["displayName"])
                    elif isinstance(item, str):
                        vals.append(item)
                display_value = ", ".join(vals) if vals else None
            elif isinstance(raw_value, str):
                display_value = raw_value
            else:
                display_value = str(raw_value) if raw_value is not None else None

            if display_value is not None and display_value != "":
                custom_fields[field_id] = {
                    "id": field_id,
                    "name": display_name,
                    "value": display_value,
                    "rendered": rendered_value,
                    "type": field_schema.get("type", "unknown"),
                }

    result = {
        "ticketId": ticket_id,
        "fetchTimestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "basic": {
            "summary": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "descriptionRendered": rendered.get("description", ""),
            "priority": fields.get("priority", {}).get("name", ""),
            "status": fields.get("status", {}).get("name", ""),
            "issuetype": fields.get("issuetype", {}).get("name", ""),
            "assignee": (
                fields.get("assignee", {}).get("displayName", "")
                if fields.get("assignee") else ""
            ),
            "reporter": (
                fields.get("reporter", {}).get("displayName", "")
                if fields.get("reporter") else ""
            ),
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "labels": fields.get("labels", []),
            "components": [
                c["name"] for c in fields.get("components", []) if c.get("name")
            ],
            "fixVersions": [
                v["name"] for v in fields.get("fixVersions", []) if v.get("name")
            ],
        },
        "customFields": custom_fields,
        "epic": None,
        "linkedIssues": linked if isinstance(linked, list) else [],
        "subtasks": subtasks if isinstance(subtasks, list) else [],
        "comments": comments if isinstance(comments, list) else [],
        "changelog": changelog if isinstance(changelog, list) else [],
        "attachments": attachments if isinstance(attachments, list) else [],
        "agile": agile if isinstance(agile, dict) else {},
    }

    if isinstance(epic, dict) and epic.get("key"):
        epic_fields = epic.get("fields", {})
        result["epic"] = {
            "key": epic.get("key", ""),
            "summary": epic_fields.get("summary", ""),
            "status": epic_fields.get("status", {}).get("name", ""),
            "priority": epic_fields.get("priority", {}).get("name", ""),
            "issuetype": epic_fields.get("issuetype", {}).get("name", ""),
        }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
