"""Ollama API client for local embeddings and structured generation."""

from typing import Any, TypeVar

import requests
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class OllamaConnectionError(Exception):
    """Raised when the Ollama service cannot be reached."""


class OllamaClient:
    """HTTP client for the Ollama REST API."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def generate_embedding(self, model: str, text: str) -> list[float]:
        """Generate an embedding vector for the provided text."""
        url = f"{self.base_url}/api/embeddings"
        payload: dict[str, Any] = {"model": model, "prompt": text}
        try:
            response = self._session.post(url, json=payload, timeout=60)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            raise OllamaConnectionError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc

        response.raise_for_status()
        data = response.json()
        return [float(value) for value in data["embedding"]]

    def generate_structured(self, model: str, prompt: str, schema: type[T]) -> T:
        """Generate a response and validate it against the Pydantic schema."""
        url = f"{self.base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
        }
        try:
            response = self._session.post(url, json=payload, timeout=120)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            raise OllamaConnectionError(f"Failed to connect to Ollama at {self.base_url}: {exc}") from exc

        response.raise_for_status()
        data = response.json()
        content = data["message"]["content"]

        try:
            return schema.model_validate_json(content)
        except ValidationError as exc:
            raise ValueError(f"Ollama response did not match schema: {exc}") from exc
