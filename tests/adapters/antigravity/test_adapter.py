import pytest

from router.adapters.antigravity.adapter import AntigravityAdapter, SubprocessResult
from router.domain.errors import ProviderError
from router.domain.port import ProviderConfig
from router.domain.transcript import Transcript


def make_adapter(run, max_attempts=2, on_empty_output=True):
    return AntigravityAdapter(
        run_subprocess=run,
        retry_max_attempts=max_attempts,
        retry_on_empty_output=on_empty_output,
    )


async def test_send_returns_response_text_on_success():
    async def run(args):
        return SubprocessResult(exit_code=0, stdout="Hello there", stderr="")

    adapter = make_adapter(run)
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    response = await adapter.send(transcript, ProviderConfig(model="gemini-3-pro"))

    assert response.text == "Hello there"
    assert response.stream is None


async def test_send_passes_flattened_transcript_and_model_as_cli_args():
    captured_args = []

    async def run(args):
        captured_args.append(args)
        return SubprocessResult(exit_code=0, stdout="ok", stderr="")

    adapter = make_adapter(run)
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    await adapter.send(transcript, ProviderConfig(model="gemini-3-pro"))

    args = captured_args[0]
    assert args[0] == "agy"
    assert "-p" in args
    assert "User: Hi" in args[args.index("-p") + 1]
    assert "--model" in args
    assert "gemini-3-pro" in args


async def test_send_retries_once_on_empty_output_then_succeeds():
    calls = []

    async def run(args):
        calls.append(1)
        if len(calls) == 1:
            return SubprocessResult(exit_code=0, stdout="", stderr="")
        return SubprocessResult(exit_code=0, stdout="Hello", stderr="")

    adapter = make_adapter(run, max_attempts=2)
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    response = await adapter.send(transcript, ProviderConfig(model="gemini-3-pro"))

    assert response.text == "Hello"
    assert len(calls) == 2


async def test_send_raises_after_exhausting_retries_on_empty_output():
    calls = []

    async def run(args):
        calls.append(1)
        return SubprocessResult(exit_code=0, stdout="", stderr="")

    adapter = make_adapter(run, max_attempts=2)
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    with pytest.raises(ProviderError):
        await adapter.send(transcript, ProviderConfig(model="gemini-3-pro"))

    assert len(calls) == 2


async def test_send_does_not_retry_when_on_empty_output_is_false():
    calls = []

    async def run(args):
        calls.append(1)
        return SubprocessResult(exit_code=0, stdout="", stderr="")

    adapter = make_adapter(run, max_attempts=3, on_empty_output=False)
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    response = await adapter.send(transcript, ProviderConfig(model="gemini-3-pro"))

    assert response.text == ""
    assert len(calls) == 1
