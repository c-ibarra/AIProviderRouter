## Why

Today, switching between Claude and Antigravity for personal work means manually opening a different CLI/IDE session — there's no single entry point that lets Warp (or any OpenAI-compatible client) talk to whichever provider is configured, without hardcoding a vendor. The architecture, provider integrations, and every major trade-off have already been decided and documented (`openspec/PROJECT_SPEC.md`, ADR-0001/0002/0003); what's missing is the actual implementation.

## What Changes

- Add a local FastAPI service exposing an OpenAI-compatible `/v1/chat/completions` endpoint, bound to `127.0.0.1` only, registered as a custom endpoint in Warp.
- Add a `ProviderPort` interface (hexagonal core) that the HTTP layer depends on instead of any specific provider SDK/CLI.
- Add a `ClaudeAdapter` implementing `ProviderPort` via `claude-agent-sdk` — native multi-turn, native SSE streaming.
- Add an `AntigravityAdapter` implementing `ProviderPort` via the `agy` CLI's `-p`/`--print` mode as a subprocess — stateless single-turn per call, transcript flattened into a plain `System:`/`User:`/`Assistant:` string, one automatic retry (configurable) on the known "exit 0, empty stdout" bug, single simulated SSE chunk in the response.
- Load provider selection from `config/provider.yaml` fresh on every request (`default_provider` only — no per-message routing rules; there's no field in the OpenAI request shape to carry one).
- Fail fast at process startup if `claude` or `agy` aren't installed/logged in.
- Log full request/response content (configurable log level) to `~/Library/Logs/ai-provider-router/router.log`.
- No tool/file/command execution on either provider leg (chat-only, no agentic side effects) — this is a v1 scope limit, not a missing feature to backfill silently.

## Capabilities

### New Capabilities
- `provider-router-api`: the FastAPI driving adapter — OpenAI-compatible `/v1/chat/completions` (request parsing, transcript assembly, SSE response framing), `provider.yaml` loading/validation, startup fail-fast checks, logging.
- `claude-adapter`: the `ProviderPort` implementation backed by `claude-agent-sdk` — native streaming, multi-turn capable (though unused statelessly per ADR-0003).
- `antigravity-adapter`: the `ProviderPort` implementation backed by the `agy` CLI subprocess — transcript flattening, empty-output detection and retry, single-chunk response framing.

### Modified Capabilities
(none — this is the first implementation; no existing specs to modify)

## Impact

- **New code:** `router/domain/` (the `ProviderPort` interface, transcript serialization, retry policy), `router/adapters/claude/`, `router/adapters/antigravity/`, `router/adapters/http/`.
- **Existing files touched:** none of the router's own source yet exists; `router/route.py` (the earlier CLI-passthrough placeholder) is superseded and can be removed once this lands.
- **Dependencies added:** `fastapi`, `uvicorn`, `claude-agent-sdk`, `pyyaml` (already used by the placeholder).
- **External requirements:** `claude` and `agy` CLIs installed and logged in on the host machine; no dependency on any provider's HTTP API.
