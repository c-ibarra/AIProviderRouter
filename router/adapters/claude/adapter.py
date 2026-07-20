"""ClaudeAdapter: ProviderPort backed by the official claude-agent-sdk.

No subprocess — the SDK talks to Claude Code in-process. Stateless (ADR-0003):
no `resume=`/session tracking, every request builds a fresh prompt from the
transcript. The system message uses the SDK's native `system_prompt` option;
prior turns are flattened into the prompt text (design.md D3 amendment —
the SDK's structured multi-message input is for streaming a live queue of
user turns, not for replaying a fixed prior history with assistant turns)."""

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock
from claude_agent_sdk import query as sdk_query

from router.domain.port import ProviderConfig, ProviderPort, ProviderResponse
from router.domain.transcript import Transcript


class ClaudeAdapter(ProviderPort):
    def __init__(self, query_fn=None):
        self._query_fn = query_fn or sdk_query

    async def send(self, transcript: Transcript, config: ProviderConfig) -> ProviderResponse:
        prompt = transcript.flatten_turns_only()
        options = ClaudeAgentOptions(system_prompt=transcript.system, model=config.model)

        async def token_stream():
            async for message in self._query_fn(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            yield block.text

        if config.want_stream:
            return ProviderResponse(text="", stream=token_stream())

        text = "".join([chunk async for chunk in token_stream()])
        return ProviderResponse(text=text, stream=None)
