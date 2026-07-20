"""ProviderPort: the hexagonal core's boundary to a provider adapter (ADR-0002)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from router.domain.transcript import Transcript


@dataclass
class ProviderConfig:
    """Per-provider settings resolved from provider.yaml for a single request.

    `want_stream` reflects whether the caller's request asked for `stream: true`.
    AntigravityAdapter always ignores it (agy -p has no incremental output);
    ClaudeAdapter branches on it to decide whether to return a live `stream`
    or fully collect the response into `text` (design.md D3 amendment).
    """

    model: str
    effort: str | None = None
    want_stream: bool = False


@dataclass
class ProviderResponse:
    """Result of a ProviderPort.send() call.

    `stream` is set only when the adapter can emit incremental tokens (Claude).
    When it's None, the HTTP layer frames `text` as a single SSE chunk.
    """

    text: str
    stream: AsyncIterator[str] | None = None


class ProviderPort(ABC):
    """One method: send a transcript, get a response. Both adapters implement only this."""

    @abstractmethod
    async def send(self, transcript: Transcript, config: ProviderConfig) -> ProviderResponse: ...
