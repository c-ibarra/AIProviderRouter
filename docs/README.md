# ai-provider-router

A local, config-driven router between **Claude** and **Antigravity** — a single OpenAI-compatible endpoint that Warp (or any OpenAI-compatible client) can call, with the actual provider decided by `config/provider.yaml` rather than hardcoded into the client.

See [`openspec/PROJECT_SPEC.md`](../openspec/PROJECT_SPEC.md) for the full specification, and [`docs/adr/`](adr/) for the architecture decisions behind it. See [`DISCLAIMER.md`](DISCLAIMER.md) for the compliance/usage disclaimer.

## Prerequisites

- Python 3.14+ and [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and logged in (`claude` on `PATH`, `claude login` run once)
- [Antigravity CLI](https://antigravity.google/cli) installed and logged in (`agy` on `PATH`, `agy login` run once)

Both providers authenticate via their own local OAuth session — the router never stores or requests API keys or credentials of its own (see `docs/adr/0001-antigravity-cli-over-sdk.md`).

## Setup

```sh
uv sync
```

## Configuration

Edit [`config/provider.yaml`](../config/provider.yaml). The only thing that determines which provider handles requests is `default_provider` — there's no per-message routing (the OpenAI request shape has no field for it). The file is re-read on every request, so changes take effect immediately, no restart needed.

## Running

```sh
uv run python -m router.adapters.http.main
```

This validates that `claude` and `agy` are on `PATH` before serving traffic (fails fast with a clear error otherwise), then listens on `http://127.0.0.1:8000` only — never on a network-reachable interface.

To start it automatically the first time you open a new Warp session, see [`scripts/start-router.sh`](../scripts/start-router.sh) and wire it into your shell startup config.

Logs (full request/response content, for debugging) go to `~/Library/Logs/ai-provider-router/router.log`.

## Using it from Warp

Add a custom endpoint in Warp pointing at `http://127.0.0.1:8000/v1`, with model name `ai-provider-router`. No API key is required (the router only checks that requests come from `127.0.0.1`).

## Testing

```sh
uv run pytest
```

## Architecture

Hexagonal (ports & adapters) — see `docs/adr/0002-hexagonal-architecture.md`. A `ProviderPort` interface with two adapters:

- **Claude** — official `claude-agent-sdk`, in-process, real SSE streaming.
- **Antigravity** — official `agy` CLI's headless `-p` mode via subprocess, single-chunk responses.

Both legs are stateless: every request forwards the caller's full message history as a fresh transcript, with no server-side session store (`docs/adr/0003-stateless-chat-only-scope.md`). Neither leg has file/command tool access — this is a chat-only endpoint, not a way to drive agentic file edits remotely.

## Disclaimer

Educational/portfolio project. Not affiliated with or endorsed by Anthropic or Google. See [`DISCLAIMER.md`](DISCLAIMER.md) for the full text.
