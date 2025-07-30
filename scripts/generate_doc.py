#!/usr/bin/env python3
"""
Convert connector manifest (JSON or YAML) to Markdown via Jinja2 template.

Usage:
    python scripts/generate_doc.py [--ai] [--draft] <src_manifest> [<dst_path>]
Examples:
    python scripts/generate_doc.py manifests/salesforce.json docs/connectors/salesforce.md
    python scripts/generate_doc.py --ai manifests/salesforce.json docs/connectors/salesforce.md
    python scripts/generate_doc.py --draft manifests/salesforce.json
    python scripts/generate_doc.py --draft --ai manifests/salesforce.json
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

def main(src: str, dst: str, use_ai: bool=False):
    src_p, dst_p = Path(src), Path(dst)
    if use_ai:
        # Enrich manifest with AI before rendering
        import sys, os
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        from enrich_manifest import enrich_manifest
        manifest = load_manifest(src_p)
        manifest = enrich_manifest(manifest)
        data = manifest
    else:
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
    # Use plain ASCII to avoid UnicodeEncodeError on some Windows consoles
    print(f"[ok] {dst_p} created.")

if __name__ == "__main__":
    args = sys.argv[1:]
    use_ai = False
    draft = False
    # Parse flags --ai and --draft
    while args and args[0] in ("--ai", "--auto", "--draft"):
        flag = args.pop(0)
        if flag in ("--ai", "--auto"):
            use_ai = True
        elif flag == "--draft":
            draft = True
    # Determine source and destination paths
    if draft:
        if len(args) != 1:
            print(main.__doc__)
            sys.exit(1)
        src = args[0]
        slug = Path(src).stem
        dst = f"docs/drafts/{slug}.md"
    else:
        if len(args) != 2:
            print(main.__doc__)
            sys.exit(1)
        src, dst = args
    main(src, dst, use_ai)
