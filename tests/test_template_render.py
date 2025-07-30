import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Helper to render the connector template
 def render_template(manifest: dict) -> str:
     env = Environment(
         loader=FileSystemLoader("templates"),
         autoescape=select_autoescape()
     )
     tpl = env.get_template("connector.md.j2")
     return tpl.render(**manifest)

 def test_placeholder_for_missing_description():
     manifest = {
         "displayName": "Test Connector",
         "long_description": "Description",
         "prereq_steps": [],
         "setup_fields": [{"name": "f1", "description": ""}],
         "auth_params": [{"name": "a1", "type": "String", "default": "", "example": "", "description": ""}],
         "task_params": [{"name": "t1", "type": "String", "default": "", "example": "", "description": ""}],
         "tables": [],
         "generation_ts": "2025-01-01T00:00:00Z"
     }
     output = render_template(manifest)
     # All sections with missing descriptions should show the TODO marker
     assert output.count("⚠️ TODO") >= 3