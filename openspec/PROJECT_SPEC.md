# AI Provider Router — Project Specification (OpenSpec)

> **Disclaimer:** Educational/study project. Not affiliated with or endorsed by Anthropic or Google. Use at your own risk.

## 1. Executive Summary

**Project name:** `ai-provider-router`

Documents and implements a local, configurable workflow to work with **Claude** and **Antigravity**, selecting the provider via configuration rather than hardcoding a vendor. The router itself exposes a local OpenAI-compatible `/v1/chat/completions` endpoint (consumed by Warp as a custom endpoint); it does not call either provider's own HTTP API directly.

- **Claude:** author's own authenticated local Claude Code (OAuth) session, driven via the official `claude-agent-sdk`.
- **Antigravity:** author's own authenticated local Antigravity (OAuth) session, driven via the official `agy` CLI's headless mode.

No shared network service, no multiple external users. Intended as a portfolio/educational project, not a commercial product.

## 2. Disclaimer and Compliance

**Claude (Anthropic):** local OAuth session only for personal, ordinary use; Claude.ai login; no token extraction/hacking; migrate to official API key if ever serving other users.

**Antigravity (Google):** official auth OAuth session; must comply with Google's Prohibited Use Policy for the underlying **Gemini API**; credentials never shared.

**Allowed authentication matrix:**

| Scenario                    | Claude local OAuth      | Antigravity official method |
| ---------------------------- | ------------------------ | ---------------------------- |
| Personal work on my Mac      | **Allowed — in scope**   | **Allowed — in scope**       |
| Local automation for myself  | Allowed with caution      | Allowed                      |

**Antigravity authentication (resolved, ADR-0001):** the router integrates Antigravity via the official `agy` CLI's headless `-p`/`--print` mode, authenticated through the same free consumer OAuth session established interactively via `agy login` (OS keyring, no API key). Two alternatives were evaluated and rejected: the official `antigravity-sdk-python` SDK (its only auth paths — `GeminiAPIEndpoint` and `VertexEndpoint` — require either a provisioned Gemini API key or GCP Application Default Credentials, neither a free consumer OAuth reuse) and community OAuth-bridging tools such as `opencode-antigravity-auth` (calls undocumented internal Antigravity/Cloud Code endpoints; its own README states this violates Google's Terms of Service and cites account-ban reports — incompatible with this project's compliance-by-design goal). Full rationale: `docs/adr/0001-antigravity-cli-over-sdk.md`.

## 3. Objectives

**Functional:** personal, reproducible workflow using either Claude or Antigravity, selected by config.
**Portfolio:** demonstrate multi-provider architecture, compliance-by-design across two vendors, clear documentation.
**Non-objectives:** not SaaS, no multi-user, no public endpoints, doesn't redistribute either provider.

## 4. Technical Architecture

**Overview:** Warp (custom endpoint) → **Provider Router** (local FastAPI service, OpenAI-compatible `/v1/chat/completions`, bound to `127.0.0.1` only) → `ProviderPort` interface → **`ClaudeAdapter`** (`claude-agent-sdk`, in-process, native streaming + multi-turn) **or** **`AntigravityAdapter`** (`agy` CLI subprocess, single-chunk response) → shared Config Layer (`provider.yaml`, re-read every request).

The router is structured as **hexagonal architecture (ports & adapters)** — see `docs/adr/0002-hexagonal-architecture.md`. The core (provider selection from config, transcript serialization, retry policy) depends only on the `ProviderPort` interface, never on a specific SDK or CLI. This isn't speculative abstraction: the two adapters are two already-different, already-built integrations (SDK call vs. subprocess), so the port just names a shape that already exists.

**Components:**

| Component                                     | Status                                          |
| ---------------------------------------------- | ------------------------------------------------ |
| Claude adapter (`claude-agent-sdk`)            | Implemented, tested (TDD)                         |
| Antigravity adapter (`agy` subprocess)         | Implemented, tested (TDD)                         |
| Provider Router (FastAPI, OpenAI-compatible)   | Implemented, tested (TDD)                         |
| Config Layer (`provider.yaml`)                 | Implemented, tested                               |
| Startup guard (`scripts/start-router.sh`)      | Implemented, manually verified — not yet wired into the user's shell config |
| CLAUDE.md per project                          | Outside router scope (see FR-06)                  |
| Compliance Guard                               | Manual + config checks                            |

**Stack:** Python, FastAPI, `claude-agent-sdk`, `agy` CLI (Antigravity), `uv`, `pytest`, Warp, PyCharm, YAML/JSON/Markdown config, Git.

**Directory structure:**
```
ai-provider-router/
  openspec/PROJECT_SPEC.md
  docs/README.md
  docs/DISCLAIMER.md
  docs/adr/0001-antigravity-cli-over-sdk.md
  docs/adr/0002-hexagonal-architecture.md
  docs/adr/0003-stateless-chat-only-scope.md
  docs/research/antigravity-headless-invocation.md
  config/provider.yaml
  scripts/start-router.sh
  router/
    domain/            # ProviderPort, ProviderConfig/ProviderResponse, Transcript, retry helper
    adapters/
      claude/          # ClaudeAdapter (claude-agent-sdk)
      antigravity/     # AntigravityAdapter (agy CLI subprocess)
      http/            # FastAPI app, config loader, startup checks, logging, entrypoint
  tests/               # mirrors router/, pytest + pytest-asyncio
  pyproject.toml
```

Note: earlier drafts of this spec planned `claude/settings.example.json`, `claude/CLAUDE.md.template`, `antigravity/antigravity.env.example`, and `examples/workflow-personal-local-{claude,antigravity}.md`. These were removed as unused once the design settled: FR-06 (per-project CLAUDE.md/GEMINI.md context) turned out to be out of scope for a chat-only router with no `cwd`, and `antigravity.env.example` implied an API-key `.env` flow that ADR-0001 explicitly rejected in favor of `agy login` OAuth.

**provider.yaml** (see `config/provider.yaml` for the live version):
```yaml
default_provider: antigravity

providers:
  claude:
    auth_source: local_oauth
    scope: personal_only
    model: claude-sonnet-5     # passed as --model
    effort: medium              # passed as --effort (low|medium|high|xhigh|max)

  antigravity:
    auth_source: local_oauth
    scope: personal_only
    model: gemini-3-pro          # passed as --model; no --effort equivalent —
                                   # reasoning/thinking level is a model variant, not a flag
    retry:
      max_attempts: 2             # 1 automatic retry, then an explicit error
      on_empty_output: true       # "exit 0, empty stdout" counts as a failure

# Routing is 100% config-driven: default_provider handles every request.
# There's no per-message routing — OpenAI's chat-completions request shape
# (what Warp sends) has no field to carry a "task type" signal, so per-task
# routing rules would be dead code. Switch providers by editing this file;
# it's re-read on every request, no restart needed.
```

**Provider integration shape (resolved):** Claude is driven via the official `claude-agent-sdk` (Python, no subprocess, native multi-turn `resume=` support, native async streaming). Antigravity is driven via the official `agy` CLI's `-p`/`--print` mode wrapped as a subprocess. The two provider legs are intentionally asymmetric, each using the best available officially-supported, ToS-compliant integration for that provider today.

**Scope: stateless and tool-free (resolved, ADR-0003).** The router keeps no session store — every request forwards the caller's full message history as a fresh transcript (Warp already sends full history per the OpenAI contract), rather than mapping conversations to a provider-side session ID. All file/command tools are disabled on both legs (chat-only; no agentic side effects). Antigravity's `agy -p` has no structured multi-message input or system-prompt flag, so the full transcript (system message, if any, plus every turn) is flattened into a single string using a plain `System:`/`User:`/`Assistant:` format before being passed to `-p`.

**Streaming (resolved):** real SSE streaming for the Claude leg (near-free given `claude-agent-sdk`'s `AsyncIterator[Message]`); the Antigravity leg returns its complete response as a single simulated SSE chunk, since `agy -p` isn't confirmed to emit incremental output. Documented asymmetry, not a blocker.

**Reliability (resolved):** `agy -p` has a documented history of returning exit 0 with empty stdout in non-TTY/subprocess contexts (GitHub Issue #76 on the official repo — see `docs/research/antigravity-headless-invocation.md`). The router treats that as a failure, retries automatically (`retry.max_attempts` in `provider.yaml`, default 2 — i.e. one retry), and returns an explicit error to the caller if every attempt comes back empty.

**Operational details (resolved):**
- **Startup:** validates at process start that both `claude` and `agy` are installed and logged in, failing fast with a clear error.
- **Process lifecycle:** started via a guard in `.zshrc` (checks if the router is already running — pidfile/port check — and starts it in background if not), not a `launchd` agent or Warp's legacy Launch Configurations.
- **Router auth:** none beyond binding to `127.0.0.1` — no API key layer on top.
- **Logging:** full request/response content logged by default (not just metadata), with a configurable log level, to `~/Library/Logs/ai-provider-router/router.log`.
- **Model name in Warp:** the custom endpoint is registered with model name `ai-provider-router`.

## 5. Functional Specification

**Actors:** User (me), Claude Code CLI, Antigravity Adapter, Project repository.

**Use cases:** UC-01 Start Claude session, UC-02 Configure Antigravity access, UC-03 Select provider via config, UC-04 Work on dev task, UC-05 Re-auth Claude, UC-06 Rotate Antigravity key.

**Functional requirements:** FR-01–05 covering Claude session, Antigravity session, provider selection via config. **FR-06 (CLAUDE.md/GEMINI.md per-project context) is out of scope for the router**: it runs in chat-only mode with no file access and no project `cwd`, so it has no use for per-project context files. `CLAUDE.md`/`GEMINI.md` still apply normally when working directly with Claude Code or Antigravity IDE on other projects — just not through this router.

**Non-functional requirements:** NFR-01–05 covering local-only processing, no plaintext secrets, reproducibility, visible disclaimer, compliance enforced by design.

## 6. Portfolio Roadmap

| Phase | Content                                          | Status      |
| ----- | ------------------------------------------------- | ----------- |
| 1     | Document reference architecture                    | Done        |
| 2     | Implement provider.yaml loader + Router            | Pending     |
| 3     | Publish repo with templates for both providers     | Pending     |
| 4     | Architecture diagram + compliance write-up         | Done — `docs/architecture.md`, `docs/DISCLAIMER.md` |
| 5     | Multi-user gateway (separate project)              | Not planned |

## 7. Full Disclaimer

```
Educational/study project. Not affiliated with or endorsed by
Anthropic or Google. Uses Claude Code (own OAuth session) or
Antigravity (own OAuth session or similar),
selected via configuration. Follows Anthropic's terms and Google's
Prohibited Use Policy for the Gemini API. No network service, no
proxying, no shared credentials.
```

## 8. References
- Claude Code — Authentication, Legal & Compliance, Settings docs (Anthropic)
- Google — Antigravity docs (official)
- **Gemini API** — OpenAI Compatibility, Usage Policies (Google)
- `docs/adr/0001-antigravity-cli-over-sdk.md` — why `agy` CLI over the official SDK
- `docs/adr/0002-hexagonal-architecture.md` — ports & adapters shape
- `docs/adr/0003-stateless-chat-only-scope.md` — stateless, tool-free v1 scope
- `docs/research/antigravity-headless-invocation.md` — primary-source research on `agy` headless invocation
