import os
import sys
import types
import pytest
from scripts.llm_client import get_llm_client, OpenAIClient, OllamaClient, InternalLLMClient

# Tests for LLM client factory

def test_get_openai_client(monkeypatch):
    # Stub openai module
    openai_mod = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, 'openai', openai_mod)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_TOKEN", "token")
    client = get_llm_client()
    assert isinstance(client, OpenAIClient)


def test_get_ollama_client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_ENDPOINT", "http://example.com/api/generate")
    client = get_llm_client()
    assert isinstance(client, OllamaClient)


def test_get_internal_client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "internal")
    monkeypatch.setenv("LLM_ENDPOINT", "http://example.com/api/generate")
    monkeypatch.setenv("LLM_TOKEN", "token")
    client = get_llm_client()
    assert isinstance(client, InternalLLMClient)


def test_production_restrictions(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_TOKEN", "token")
    with pytest.raises(RuntimeError):
        get_llm_client()