"""FastAPI driving adapter: OpenAI-compatible POST /v1/chat/completions.

Depends only on ProviderPort (ADR-0002) — never imports a specific SDK/CLI
directly. Provider selection is 100% config-driven (default_provider),
re-read fresh on every request (design.md D5)."""

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from router.adapters.antigravity.adapter import AntigravityAdapter
from router.adapters.claude.adapter import ClaudeAdapter
from router.adapters.http.config import ProviderSettings, load_config
from router.adapters.http.logging_config import LOGGER_NAME
from router.adapters.http.schemas import ChatCompletionRequest
from router.domain.errors import ProviderError
from router.domain.port import ProviderConfig, ProviderPort
from router.domain.transcript import Transcript

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "provider.yaml"

logger = logging.getLogger(LOGGER_NAME)

AdapterFactory = Callable[[ProviderSettings], ProviderPort]


def default_adapter_factories() -> dict[str, AdapterFactory]:
    return {
        "claude": lambda settings: ClaudeAdapter(),
        "antigravity": lambda settings: AntigravityAdapter(
            retry_max_attempts=settings.retry_max_attempts,
            retry_on_empty_output=settings.retry_on_empty_output,
        ),
    }


def _chat_completion_json(text: str, model: str) -> dict:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }


async def _sse_from_tokens(
    tokens: AsyncIterator[str], model: str, request_log: str
) -> AsyncIterator[str]:
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    collected = []
    async for token in tokens:
        collected.append(token)
        chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"
    logger.info("request=%s response=%s", request_log, "".join(collected))


async def _single_token(text: str) -> AsyncIterator[str]:
    yield text


def create_app(
    config_path: Path = DEFAULT_CONFIG_PATH,
    adapter_factories: dict[str, AdapterFactory] | None = None,
) -> FastAPI:
    factories = adapter_factories or default_adapter_factories()
    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def chat_completions(request: ChatCompletionRequest):
        router_config = load_config(config_path)
        settings = router_config.providers[router_config.default_provider]
        adapter = factories[router_config.default_provider](settings)

        transcript = Transcript.from_messages([m.model_dump() for m in request.messages])
        provider_config = ProviderConfig(
            model=settings.model,
            effort=settings.effort,
            want_stream=request.stream,
        )
        request_log = json.dumps([m.model_dump() for m in request.messages])

        try:
            response = await adapter.send(transcript, provider_config)
        except ProviderError as exc:
            logger.info("request=%s error=%s", request_log, exc)
            return JSONResponse(
                status_code=502,
                content={"error": {"message": str(exc), "type": "provider_error"}},
            )

        if response.stream is not None:
            return StreamingResponse(
                _sse_from_tokens(response.stream, request.model, request_log),
                media_type="text/event-stream",
            )
        if request.stream:
            return StreamingResponse(
                _sse_from_tokens(_single_token(response.text), request.model, request_log),
                media_type="text/event-stream",
            )
        logger.info("request=%s response=%s", request_log, response.text)
        return JSONResponse(_chat_completion_json(response.text, request.model))

    return app
