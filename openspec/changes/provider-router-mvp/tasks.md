## 1. Domain (ports & shared logic)

- [x] 1.1 Define `ProviderPort` (ABC) and `ProviderResponse` in `router/domain/port.py`
- [x] 1.2 Implement `Transcript` construction from OpenAI `messages[]` (system + turns) in `router/domain/transcript.py`
- [x] 1.3 Implement transcript flattening to the `System:`/`User:`/`Assistant:` string format (used by the Antigravity adapter) in `router/domain/transcript.py`
- [x] 1.4 Implement the generic retry-on-predicate helper in `router/domain/retry.py`

## 2. Antigravity adapter

- [x] 2.1 Implement `AntigravityAdapter(ProviderPort)` in `router/adapters/antigravity/adapter.py`, invoking `agy -p "<flattened transcript>"` as a subprocess
- [x] 2.2 Wire the empty-stdout detection + retry (via the domain retry helper) using `retry.max_attempts`/`on_empty_output` from `provider.yaml`
- [x] 2.3 Map a subprocess result to `ProviderResponse` (no `stream`, full text only) or an explicit error after exhausting retries

## 3. Claude adapter

- [x] 3.1 Implement `ClaudeAdapter(ProviderPort)` in `router/adapters/claude/adapter.py`, calling `claude_agent_sdk.query()` with the transcript's system prompt and turns
- [x] 3.2 Map the SDK's `AsyncIterator[Message]` to `ProviderResponse.stream` for the streaming case
- [x] 3.3 Map a non-streaming call to a complete `ProviderResponse.text`

## 4. HTTP layer

- [x] 4.1 Implement `config.py`: load and validate `config/provider.yaml` into a `RouterConfig`, called fresh per request (no process-level caching)
- [x] 4.2 Implement `startup.py`: fail-fast checks that `claude` and `agy` are on `PATH` and authenticated, run at FastAPI startup (scope note: presence-on-PATH only; a live-login check is left as a documented future improvement)
- [x] 4.3 Implement `app.py`: `POST /v1/chat/completions`, selecting the adapter from `RouterConfig.default_provider`, building the `Transcript`, and calling `ProviderPort.send()`
- [x] 4.4 Implement SSE response framing: real chunked streaming when `response.stream` is present (Claude), one simulated chunk when it isn't (Antigravity)
- [x] 4.5 Bind the FastAPI server to `127.0.0.1` only (no `0.0.0.0`)
- [x] 4.6 Implement request/response logging (full content, configurable level) to `~/Library/Logs/ai-provider-router/router.log`

## 5. Integration & cleanup

- [ ] 5.1 Manual end-to-end check: register the endpoint in Warp (model name `ai-provider-router`) and send a real message through the Claude adapter
- [ ] 5.2 Manual end-to-end check: same, through the Antigravity adapter, including a check of the empty-stdout retry path if reproducible
- [x] 5.3 Delete `router/route.py` (superseded CLI-passthrough placeholder)

## 6. Operational follow-up (not blocking apply-readiness — design.md's Migration Plan step 7)

- [ ] 6.1 Wire the `.zshrc` startup guard: `scripts/start-router.sh` (in this repo) starts the router in background, idempotently, if it isn't already running. Verified manually by the agent (started, confirmed listening on `127.0.0.1:8000`, re-run didn't duplicate the process, log file created, then stopped) — still pending: adding the actual snippet to the user's Nix-managed dotfiles source (not `~/.zshrc` directly, since that file is generated) and confirming it fires on a real new Warp session.
