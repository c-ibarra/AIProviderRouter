import textwrap

import pytest
from fastapi.testclient import TestClient

from router.adapters.http.app import create_app
from router.domain.errors import ProviderError
from router.domain.port import ProviderPort, ProviderResponse

CONFIG_YAML = textwrap.dedent(
    """
    default_provider: antigravity

    providers:
      claude:
        auth_source: local_oauth
        scope: personal_only
        model: claude-sonnet-5
        effort: medium

      antigravity:
        auth_source: local_oauth
        scope: personal_only
        model: gemini-3-pro
        retry:
          max_attempts: 2
          on_empty_output: true
    """
)


class FakeAdapter(ProviderPort):
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    async def send(self, transcript, config):
        if self._error:
            raise self._error
        return self._response


async def _token_stream(tokens):
    for token in tokens:
        yield token


def make_app(tmp_path, provider_name, adapter):
    config_path = tmp_path / "provider.yaml"
    config_path.write_text(CONFIG_YAML.replace("default_provider: antigravity", f"default_provider: {provider_name}"))
    return create_app(config_path=config_path, adapter_factories={provider_name: lambda settings: adapter})


def test_non_streaming_request_returns_chat_completion_json(tmp_path):
    adapter = FakeAdapter(response=ProviderResponse(text="Hello there", stream=None))
    app = make_app(tmp_path, "antigravity", adapter)
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "ai-provider-router", "messages": [{"role": "user", "content": "Hi"}], "stream": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["content"] == "Hello there"
    assert body["choices"][0]["message"]["role"] == "assistant"


def test_streaming_request_with_real_stream_returns_sse_chunks(tmp_path):
    adapter = FakeAdapter(response=ProviderResponse(text="", stream=_token_stream(["Hel", "lo"])))
    app = make_app(tmp_path, "claude", adapter)
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "ai-provider-router", "messages": [{"role": "user", "content": "Hi"}], "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert '"content": "Hel"' in body or '"content":"Hel"' in body
    assert body.strip().endswith("data: [DONE]")


def test_streaming_request_against_a_non_streaming_adapter_returns_single_sse_chunk(tmp_path):
    adapter = FakeAdapter(response=ProviderResponse(text="Hello there", stream=None))
    app = make_app(tmp_path, "antigravity", adapter)
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "ai-provider-router", "messages": [{"role": "user", "content": "Hi"}], "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = [line for line in response.text.split("\n\n") if line.startswith("data:") and line != "data: [DONE]"]
    assert len(events) == 1
    assert "Hello there" in events[0]


def test_provider_error_returns_502_with_error_body(tmp_path):
    adapter = FakeAdapter(error=ProviderError("agy -p returned empty output"))
    app = make_app(tmp_path, "antigravity", adapter)
    client = TestClient(app)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "ai-provider-router", "messages": [{"role": "user", "content": "Hi"}], "stream": False},
    )

    assert response.status_code == 502
    assert "agy -p returned empty output" in response.json()["error"]["message"]


def test_non_streaming_request_logs_full_request_and_response_content(tmp_path, caplog):
    adapter = FakeAdapter(response=ProviderResponse(text="Hello there", stream=None))
    app = make_app(tmp_path, "antigravity", adapter)
    client = TestClient(app)

    with caplog.at_level("INFO", logger="ai_provider_router"):
        client.post(
            "/v1/chat/completions",
            json={
                "model": "ai-provider-router",
                "messages": [{"role": "user", "content": "secret prompt content"}],
                "stream": False,
            },
        )

    log_text = "\n".join(record.message for record in caplog.records)
    assert "secret prompt content" in log_text
    assert "Hello there" in log_text


def test_streaming_request_logs_full_response_content_after_completion(tmp_path, caplog):
    adapter = FakeAdapter(response=ProviderResponse(text="", stream=_token_stream(["Hel", "lo"])))
    app = make_app(tmp_path, "claude", adapter)
    client = TestClient(app)

    with caplog.at_level("INFO", logger="ai_provider_router"):
        client.post(
            "/v1/chat/completions",
            json={
                "model": "ai-provider-router",
                "messages": [{"role": "user", "content": "stream this"}],
                "stream": True,
            },
        )

    log_text = "\n".join(record.message for record in caplog.records)
    assert "stream this" in log_text
    assert "Hello" in log_text
