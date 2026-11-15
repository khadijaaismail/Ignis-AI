"""Provider-neutral LLM clients for generated and structured responses."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from core.config import Settings, settings

LOGGER = logging.getLogger(__name__)
_MAX_RETRIES = 2
_REQUEST_TIMEOUT = 30.0


class LLMUnavailable(RuntimeError):
    """Raised when a configured LLM cannot be used."""


class LLMClient(ABC):
    """Interface shared by all LLM providers."""

    @abstractmethod
    def generate(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> str:
        """Generate a text response."""

    def generate_json(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> dict:
        """Generate and parse JSON, retrying once with a strict JSON request."""
        response = self.generate(system, messages, temperature, max_tokens)
        try:
            parsed = json.loads(response)
            if not isinstance(parsed, dict):
                raise ValueError("JSON response must be an object")
            return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            strict_messages = [
                *messages,
                {
                    "role": "user",
                    "content": "Return only one valid JSON object. No markdown or explanation.",
                },
            ]
            response = self.generate(system, strict_messages, temperature, max_tokens)
            parsed = json.loads(response)
            if not isinstance(parsed, dict):
                raise ValueError("JSON response must be an object")
            return parsed


def _is_retryable(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    if status is None:
        response = getattr(error, "response", None)
        status = getattr(response, "status_code", None)
    return status == 429 or (isinstance(status, int) and 500 <= status < 600)


def _with_retries(operation: Any) -> Any:
    for attempt in range(_MAX_RETRIES):
        try:
            return operation()
        except Exception as error:
            if not _is_retryable(error) or attempt == _MAX_RETRIES - 1:
                raise
            time.sleep(2**attempt)


class OpenAICompatibleClient(LLMClient):
    """Client for OpenAI, Groq, OpenRouter, Together, and Ollama APIs."""

    def __init__(self, config: Settings) -> None:
        from openai import OpenAI

        self._model = config.llm_model
        self._client = OpenAI(
            api_key=config.llm_api_key.get_secret_value(),
            base_url=config.llm_base_url,
            timeout=_REQUEST_TIMEOUT,
        )

    def generate(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> str:
        response = _with_retries(
            lambda: self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "system", "content": system}, *messages],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        return response.choices[0].message.content or ""


class AnthropicClient(LLMClient):
    """Client for Anthropic's Messages API."""

    def __init__(self, config: Settings) -> None:
        from anthropic import Anthropic

        self._model = config.llm_model
        self._client = Anthropic(
            api_key=config.llm_api_key.get_secret_value(),
            timeout=_REQUEST_TIMEOUT,
        )

    def generate(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> str:
        response = _with_retries(
            lambda: self._client.messages.create(
                model=self._model,
                system=system,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )


class MockClient(LLMClient):
    """Deterministic client for tests and explicitly configured offline use."""

    def generate(
        self,
        system: str,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1200,
    ) -> str:
        return '{"status": "ok", "source": "mock"}'


def get_llm(config: Settings | None = None) -> LLMClient:
    """Build the configured client or raise when live generation is unavailable."""
    config = config or settings
    provider = config.llm_provider.strip().lower()
    if config.demo_mode:
        raise LLMUnavailable("LLM generation is disabled in DEMO_MODE")
    if not provider:
        raise LLMUnavailable("LLM_PROVIDER is not configured")
    if provider != "mock" and not config.llm_api_key.get_secret_value():
        raise LLMUnavailable(f"LLM_API_KEY is required for provider {provider!r}")

    if provider == "mock":
        return MockClient()
    if provider == "openai_compatible":
        return OpenAICompatibleClient(config)
    if provider == "anthropic":
        return AnthropicClient(config)
    raise LLMUnavailable(f"Unsupported LLM_PROVIDER: {provider!r}")
