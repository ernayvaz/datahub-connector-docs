#!/usr/bin/env python3
"""
Enrich connector manifest using OpenAI API.

Usage:
    python scripts/enrich_manifest.py <src_manifest> <dst_manifest>
"""
import sys
import json
from pathlib import Path
import yaml
import os
import re
from scripts.llm_client import get_llm_client
from jsonschema import validate, RefResolver, ValidationError

SCHEMA_PATH = Path("manifests/manifest.schema.json")

def load_schema():
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    return json.loads(text)

def load_manifest(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)

def enrich_manifest(manifest: dict) -> dict:
    client = get_llm_client()

    prompt = (
        "You are a technical documentation generator. "
        "Given a connector manifest in JSON format with keys: displayName, long_description, prereq_steps, "
        "setup_fields (name, description), auth_params (name, type, default, example, description), "
        "task_params, tables (name, description, columns[name, type, description]), and images, "
        "fill in any empty or missing values with meaningful content: "
        "- long_description: a concise introduction paragraph. "
        "- prereq_steps: list at least 2 prerequisite steps. "
        "- setup_fields: add descriptive text for each field. "
        "- auth_params: provide default values, example values, and clear descriptions. "
        "- task_params: if missing, leave as empty array; otherwise fill description. "
        "- tables: for each table and column, add a human-friendly description. "
        "Return only the completed JSON manifest object without any additional explanation."
    )
    messages_json = json.dumps(manifest)
    full_prompt = prompt + "\n" + messages_json
    try:
        raw = client.generate(full_prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            print("Warning: Could not parse JSON from LLM response, skipping enrichment.")
            return manifest
    except Exception as e:
        print(f"Warning: LLM enrichment failed ({e}), skipping enrichment.")
        return manifest

def main():
    if len(sys.argv) != 3:
        print("Usage: scripts/enrich_manifest.py <src> <dst>")
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    src_p = Path(src)
    dst_p = Path(dst)

    manifest = load_manifest(src_p)
    schema = load_schema()
    try:
        validate(instance=manifest, schema=schema)
    except ValidationError as e:
        print(f"Error: manifest schema validation failed: {e}")
        sys.exit(1)

    enriched = enrich_manifest(manifest)

    dst_p.parent.mkdir(parents=True, exist_ok=True)
    dst_p.write_text(yaml.safe_dump(enriched, sort_keys=False), encoding="utf-8")
    print(f"[ok] Enriched manifest saved to {dst_p}")

if __name__ == '__main__':
    main() 