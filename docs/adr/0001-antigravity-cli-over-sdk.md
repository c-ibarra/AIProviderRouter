# Antigravity integration: CLI subprocess over official SDK

Antigravity offers two integration paths: `antigravity-sdk-python` (a native async Python SDK, the counterpart to Anthropic's `claude-agent-sdk`) and the `agy` CLI's headless `-p`/`--print` mode. We chose the CLI, wrapped as a subprocess, over the SDK.

**Why:** the SDK's only two authentication mechanisms — verified directly in `google/antigravity/models.py`: `GeminiAPIEndpoint` and `VertexEndpoint` — require either a provisioned Gemini API key or GCP Application Default Credentials. Neither reuses the free consumer OAuth session (`agy login`) that this project's compliance principles require (personal use, OAuth-only, no provisioned API keys). The `agy` CLI is the only integration path that authenticates via that same consumer OAuth session, reused transparently via the OS keyring.

We also evaluated and explicitly rejected community OAuth-bridging tools (e.g. `opencode-antigravity-auth`), which call undocumented internal Antigravity/Cloud Code endpoints. That project's own README states this "violates Google's Terms of Service" and cites user reports of account bans — incompatible with this project's compliance-by-design goal.

## Consequences

The `agy -p` CLI has two known rough edges, verified against the official `google-antigravity/antigravity-cli` repo (see `docs/research/antigravity-headless-invocation.md`):

- A documented history of non-TTY stdout bugs (mostly fixed across recent point releases, but not confirmed exhaustively) — mitigate with a pinned `agy` version plus empty-output detection and retry.
- No documented way to pre-assign or capture a conversation ID for multi-turn resume from a `--print` invocation — so the router's Antigravity leg is **stateless-only** (one turn per request) until the CLI exposes that.

The Claude leg, by contrast, uses the official `claude-agent-sdk` directly (no subprocess, native multi-turn `resume=` session support). The two provider legs are therefore intentionally asymmetric — each integrated via the best officially-supported, ToS-compliant path available today, not a matching pair.
