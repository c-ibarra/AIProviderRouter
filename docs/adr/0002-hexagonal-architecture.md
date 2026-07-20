# Hexagonal architecture (ports & adapters)

The router's core job — take a transcript, send it to a provider, return the response — has exactly two concrete implementations today (Claude via `claude-agent-sdk`, Antigravity via the `agy` CLI subprocess), each with genuinely different transports (SDK call vs. subprocess) and quirks (native multi-turn vs. stateless-only, structured system prompt vs. flattened transcript). We're structuring the router around a `ProviderPort` interface (`send(transcript, config) -> response`) with one adapter per provider, plus a driving adapter (FastAPI, exposing the OpenAI-compatible `/v1/chat/completions` endpoint) that depends only on the port, never on a specific provider's SDK/CLI.

**Why:** this isn't speculative abstraction for a hypothetical future provider — the two adapters already exist as distinct implementations today. The pattern isolates the core logic (transcript serialization, retry policy, provider selection from config) from both the HTTP framework and each provider's SDK/CLI specifics, making the core testable against a fake adapter without touching real Claude/Antigravity sessions, and making it straightforward to add a third provider later without touching the HTTP layer or the other adapters.

## Consequences

More files/indirection (a port interface, per-provider adapter modules, a composition point wiring config → adapter) than a flat `if provider == "claude"` router would need. Accepted given there are two real, already-built-different implementations behind the same operation — the shape reflects a decision already made (ADR-0001), not one anticipated.
