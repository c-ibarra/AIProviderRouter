## Context

The overall architecture, both provider integrations, and every major trade-off were already decided in a design session before this change existed (`openspec/PROJECT_SPEC.md`, ADR-0001/0002/0003, `docs/research/antigravity-headless-invocation.md`). This design translates those decisions into an implementation plan; it does not re-open them. Where this document repeats a decision from the ADRs, it's to make the plan self-contained, not to re-litigate it — genuinely new decisions made here are called out explicitly in **Decisions**.

Current state: `router/route.py` is a placeholder CLI-passthrough script from an earlier, superseded design (direct `exec` into a CLI, no HTTP layer). `config/provider.yaml` already has the target schema. No FastAPI code, no adapters, and no tests exist yet.

## Goals / Non-Goals

**Goals:**
- A local FastAPI service exposing `POST /v1/chat/completions` (OpenAI-compatible request/response shape), bound to `127.0.0.1` only.
- A `ProviderPort` interface with two adapters (`ClaudeAdapter`, `AntigravityAdapter`) selected via `config/provider.yaml`'s `default_provider`, re-read on every request.
- Real SSE streaming for the Claude leg; a single simulated SSE chunk for the Antigravity leg.
- Fail-fast startup validation (`claude` and `agy` installed and logged in).
- Full request/response logging (configurable level) to `~/Library/Logs/ai-provider-router/router.log`.

**Non-Goals (v1 scope limits, per ADR-0003 — not gaps to silently fill in):**
- No agentic tools (file edits, shell commands) on either provider leg — chat-only.
- No session store / no multi-turn resume tracking — every request is a fresh transcript built from the caller's full message history.
- No per-message routing rules (`task_type` matching) — `default_provider` is the only routing mechanism, since the OpenAI request shape has no field to carry that signal.
- No router-level auth (API key) — `127.0.0.1` binding is the only access control.

## Decisions

**D1 — Package layout mirrors the ports & adapters split (ADR-0002).**
```
router/
  domain/
    port.py            # ProviderPort (ABC): async def send(transcript, config) -> ProviderResponse
    transcript.py       # OpenAI messages[] -> internal Transcript; Transcript -> agy's flattened string
    retry.py            # generic retry-on-predicate helper, used by AntigravityAdapter
  adapters/
    claude/
      adapter.py         # ClaudeAdapter(ProviderPort) wrapping claude_agent_sdk.query()
    antigravity/
      adapter.py         # AntigravityAdapter(ProviderPort) wrapping `agy -p` via subprocess
    http/
      app.py             # FastAPI app, POST /v1/chat/completions, SSE response framing
      startup.py         # fail-fast checks (claude/agy on PATH + logged in)
      config.py           # provider.yaml loader (re-read per request), no caching across requests
```
`router/route.py` (the old CLI-passthrough placeholder) is deleted once `router/adapters/http/app.py` replaces its purpose.

**D2 — `ProviderPort` shape.**
```python
class ProviderResponse:
    text: str                       # full response text (single-chunk case)
    stream: AsyncIterator[str] | None  # token stream (Claude only); None => caller sends one SSE chunk with `text`

class ProviderPort(ABC):
    async def send(self, transcript: Transcript, config: ProviderConfig) -> ProviderResponse: ...
```
One method. Both adapters implement it; the HTTP layer never branches on which provider it's talking to — it only asks whether `response.stream` is present to decide how to frame the SSE output. This is the concrete form ADR-0002 committed to.

**D3 — Transcript serialization.** `Transcript` is built once from the request's `messages[]` (system + turns) and handed to whichever adapter is selected. `AntigravityAdapter` flattens it into a single string (`System: ...\n\nUser: ...\nAssistant: ...\n...`) before calling `agy -p "<flattened>"`, per the resolved transcript-format decision.

> **Amendment (found during implementation):** the original plan for `ClaudeAdapter` was "native structured prompt — no flattening needed." In practice, `claude_agent_sdk.query()`'s structured input (`AsyncIterable[dict]`) is documented for streaming a live queue of *new* user turns into an ongoing session, not for replaying a fixed prior history that includes synthetic assistant turns — and ADR-0003 rules out session/`resume=` state to lean on instead. `ClaudeAdapter` therefore flattens prior turns (`Transcript.flatten_turns_only()`) into the prompt string exactly like the Antigravity leg, with only the system message kept separate via `ClaudeAgentOptions(system_prompt=...)` (the one piece of native structure the SDK genuinely offers). This narrows — but doesn't erase — the asymmetry between the two adapters claimed above.

**D4 — Antigravity reliability.** `AntigravityAdapter.send()` wraps the subprocess call in the generic retry helper (D1): on `on_empty_output: true` in config, an "exit 0 + empty stdout" result is treated as a retryable failure, not a success. `retry.max_attempts` (default 2, i.e. one retry) governs attempts; the last failure surfaces as an explicit error `ProviderResponse` (or raised exception mapped to an OpenAI-style error response by the HTTP layer) rather than an empty 200.

**D5 — Config reload.** `config.py` exposes a `load_config() -> RouterConfig` function called once per incoming request (not cached at process scope) so edits to `provider.yaml` take effect on the next request with no restart, per the resolved config-reload decision.

**D6 — Startup validation.** `startup.py` runs at FastAPI startup (lifespan/startup event), shelling out to `claude --version`/equivalent and `agy --version`/equivalent (and, where feasible, a lightweight auth check) and refuses to start serving traffic if either is missing, exiting with a clear message — per the resolved fail-fast decision.

## Risks / Trade-offs

- **[Risk] `agy -p` subprocess latency per message, no context caching between calls** (identified during design discussion, ADR-0001 addendum) → **Mitigation:** accepted for v1; measure real latency once `AntigravityAdapter` exists end-to-end, revisit only if it proves unacceptable in practice (the SDK path remains a documented fallback, not implemented here).
- **[Risk] `agy -p` empty-stdout bug (GitHub Issue #76, `docs/research/antigravity-headless-invocation.md`) may not be fully fixed in whatever `agy` version is actually installed** → **Mitigation:** D4's retry-on-empty-output handles the known failure mode generically, regardless of whether the specific bug is fixed in the installed version.
- **[Risk] Full-content logging by default (resolved decision) persists potentially sensitive conversation text to disk indefinitely** → **Mitigation:** accepted trade-off (author's own machine, debuggability prioritized); log path (`~/Library/Logs/ai-provider-router/`) is outside the git repo so it can never be accidentally committed.
- **[Risk] No router-level auth** → **Mitigation:** accepted trade-off; `127.0.0.1` binding is the only defense, consistent with the resolved decision to skip an API-key layer.

## Migration Plan

1. Implement `router/domain/` (port + transcript + retry) with tests first (no adapters needed to test transcript serialization/retry logic in isolation).
2. Implement `AntigravityAdapter` against a real `agy` install (needs the CLI logged in locally to test end-to-end; unit-testable against a faked subprocess for the retry/empty-output path).
3. Implement `ClaudeAdapter` against `claude-agent-sdk`.
4. Implement the FastAPI HTTP layer wiring config → adapter selection → `ProviderPort.send()` → SSE/JSON response.
5. Delete `router/route.py` once the FastAPI app covers its use case.
6. Manual end-to-end check: register the endpoint in Warp (model name `ai-provider-router`, as resolved) and send a real message through each provider.
7. Wire the `.zshrc` startup guard (resolved decision) as a separate, small follow-up — not blocking this change's completion, since it's an operational convenience, not part of the service's own correctness.

Rollback: the change is additive (new `router/` package); reverting is deleting the new files and restoring `router/route.py`, with no data migration involved (no persistent state beyond logs).

## Open Questions

- Real-world `agy -p` latency and whether the empty-stdout bug is actually fixed in the version installed on this machine — deferred to implementation/testing (Risk section), not resolved here.
- Exact FastAPI error-response shape for provider failures (OpenAI-style `error` object fields) — left to implementation; no prior decision constrains it.
