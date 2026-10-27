"""Tests for application configuration."""

import os
from unittest.mock import patch

from app.config import Settings


def test_settings_has_ollama_base_url_field() -> None:
    """Settings exposes an Ollama base URL field."""
    settings = Settings()
    assert hasattr(settings, "ollama_base_url")
    assert settings.ollama_base_url is not None


def test_settings_default_embedding_model() -> None:
    """Default embedding model is nomic-embed-text."""
    settings = Settings()
    assert hasattr(settings, "ollama_embedding_model")
    assert settings.ollama_embedding_model == "nomic-embed-text"


def test_settings_default_generation_model() -> None:
    """Default generation model is qwen2.5:3b."""
    settings = Settings()
    assert hasattr(settings, "ollama_generation_model")
    assert settings.ollama_generation_model == "qwen2.5:3b"


def test_settings_default_ollama_base_url() -> None:
    """Default Ollama base URL points to the compose service."""
    settings = Settings()
    assert settings.ollama_base_url == "http://ollama:11434"


def test_settings_loads_from_environment_variables() -> None:
    """Settings values can be overridden by environment variables."""
    env = {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_EMBEDDING_MODEL": "custom-embed",
        "OLLAMA_GENERATION_MODEL": "custom-generate",
    }
    with patch.dict(os.environ, env, clear=False):
        settings = Settings()
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.ollama_embedding_model == "custom-embed"
        assert settings.ollama_generation_model == "custom-generate"


def test_settings_rejects_openai_api_key_field() -> None:
    """OpenAI settings are no longer part of the configuration."""
    settings = Settings()
    assert not hasattr(settings, "openai_api_key")


def test_settings_qdrant_defaults() -> None:
    """Qdrant defaults remain sensible."""
    settings = Settings()
    assert settings.qdrant_host == "qdrant"
    assert settings.qdrant_port == 6333


def test_settings_embedding_dimensions_default() -> None:
    """Default embedding dimensions match nomic-embed-text."""
    settings = Settings()
    assert settings.embedding_dimensions == 768
