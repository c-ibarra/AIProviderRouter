from claude_agent_sdk import AssistantMessage, TextBlock

from router.adapters.claude.adapter import ClaudeAdapter
from router.domain.port import ProviderConfig
from router.domain.transcript import Transcript


def make_fake_query(chunks):
    captured = {}

    async def fake_query(*, prompt, options):
        captured["prompt"] = prompt
        captured["options"] = options
        for chunk in chunks:
            yield AssistantMessage(content=[TextBlock(text=chunk)], model="claude-sonnet-5")

    return fake_query, captured


async def test_send_non_streaming_returns_full_collected_text():
    fake_query, _ = make_fake_query(["Hello", " there"])
    adapter = ClaudeAdapter(query_fn=fake_query)
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    response = await adapter.send(transcript, ProviderConfig(model="claude-sonnet-5", want_stream=False))

    assert response.text == "Hello there"
    assert response.stream is None


async def test_send_streaming_returns_a_token_stream():
    fake_query, _ = make_fake_query(["Hello", " there"])
    adapter = ClaudeAdapter(query_fn=fake_query)
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    response = await adapter.send(transcript, ProviderConfig(model="claude-sonnet-5", want_stream=True))

    assert response.stream is not None
    tokens = [token async for token in response.stream]
    assert tokens == ["Hello", " there"]


async def test_send_passes_system_prompt_and_model_via_options():
    fake_query, captured = make_fake_query(["ok"])
    adapter = ClaudeAdapter(query_fn=fake_query)
    transcript = Transcript.from_messages(
        [{"role": "system", "content": "Be terse."}, {"role": "user", "content": "Hi"}]
    )

    await adapter.send(transcript, ProviderConfig(model="claude-opus-4-8", want_stream=False))

    assert captured["options"].system_prompt == "Be terse."
    assert captured["options"].model == "claude-opus-4-8"


async def test_send_passes_flattened_turns_without_system_line_as_prompt():
    fake_query, captured = make_fake_query(["ok"])
    adapter = ClaudeAdapter(query_fn=fake_query)
    transcript = Transcript.from_messages(
        [{"role": "system", "content": "Be terse."}, {"role": "user", "content": "Hi"}]
    )

    await adapter.send(transcript, ProviderConfig(model="claude-sonnet-5", want_stream=False))

    assert captured["prompt"] == "User: Hi"
    assert "System:" not in captured["prompt"]
