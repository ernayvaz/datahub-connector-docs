#!/usr/bin/env python3
"""
Convert connector manifest (JSON or YAML) to Markdown via Jinja2 template.

Usage:
    python scripts/generate_doc.py manifests/salesforce.json \
           docs/connectors/salesforce.md
"""
import sys, json, datetime, pathlib
from pathlib import Path

import yaml          # PyYAML
from jinja2 import Environment, FileSystemLoader, select_autoescape

# -----------------------------------------------------------------------------
def load_manifest(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)

def main(src: str, dst: str):
    src_p, dst_p = Path(src), Path(dst)
    data = load_manifest(src_p)

    # Fall-back empty lists
    data.setdefault("prereq_steps", [])
    data.setdefault("setup_fields", [])
    data.setdefault("auth_params", [])
    data.setdefault("task_params", [])
    data.setdefault("tables", [])

    data["generation_ts"] = datetime.datetime.utcnow().isoformat() + "Z"

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape()
    )
    tpl = env.get_template("connector.md.j2")
    markdown = tpl.render(**data)

    dst_p.parent.mkdir(parents=True, exist_ok=True)
    dst_p.write_text(markdown, encoding="utf-8")
    print(f"✅  {dst_p} created.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(main.__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
