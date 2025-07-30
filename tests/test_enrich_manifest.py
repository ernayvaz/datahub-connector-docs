import sys
import pytest
from scripts.enrich_manifest import main

def test_schema_validation_fails(tmp_path, monkeypatch):
    # Create a manifest missing required 'slug' field
    bad_manifest = tmp_path / "bad.yaml"
    bad_manifest.write_text("displayName: Test Connector", encoding="utf-8")
    output_file = tmp_path / "out.yaml"
    # Ensure environment is development and internal LLM to bypass external calls
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("LLM_PROVIDER", "internal")
    monkeypatch.setenv("LLM_ENDPOINT", "http://example.com")
    monkeypatch.setenv("LLM_TOKEN", "token")
    # Simulate CLI invocation
    monkeypatch.setattr(sys, 'argv', ["enrich_manifest.py", str(bad_manifest), str(output_file)])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1