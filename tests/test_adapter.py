import pytest

from core.config import Settings
from llm.adapter import LLMUnavailable, get_llm


def test_mock_provider_generates_and_parses_deterministic_json():
    client = get_llm(Settings(_env_file=None, llm_provider="mock"))

    assert client.generate("system", [{"role": "user", "content": "hello"}]) == (
        '{"status": "ok", "source": "mock"}'
    )
    assert client.generate_json("system", []) == {"status": "ok", "source": "mock"}


def test_generate_json_retries_with_strict_instruction(monkeypatch):
    client = get_llm(Settings(_env_file=None, llm_provider="mock"))
    responses = iter(["not json", '{"answer": "ok"}'])
    calls = []

    def generate(system, messages, temperature=0.1, max_tokens=1200):
        calls.append(messages)
        return next(responses)

    monkeypatch.setattr(client, "generate", generate)

    assert client.generate_json("system", []) == {"answer": "ok"}
    assert calls[1][-1]["content"].startswith("Return only one valid JSON")


def test_demo_mode_makes_llm_unavailable():
    with pytest.raises(LLMUnavailable):
        get_llm(Settings(_env_file=None, llm_provider="mock", demo_mode=True))


def test_non_mock_provider_requires_api_key():
    with pytest.raises(LLMUnavailable):
        get_llm(
            Settings(
                _env_file=None,
                llm_provider="openai_compatible",
                llm_model="test-model",
            )
        )
