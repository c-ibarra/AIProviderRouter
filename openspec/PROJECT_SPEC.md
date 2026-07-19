# AI Provider Router — Project Specification (OpenSpec)

> **Disclaimer:** Educational/study project. Not affiliated with or endorsed by Anthropic or Google. Use at your own risk.

## 1. Executive Summary

**Project name:** `ai-provider-router`

Documents and implements a local, configurable workflow to work with **Claude** and **Antigravity**, selecting the provider via configuration rather than hardcoding a vendor.

- **Claude:** author's own authenticated local Claude Code (OAuth) session and the OpenAI-compatible endpoint.
- **Antigravity:** official authentication method (Antigravity session and the OpenAI-compatible endpoint).

No shared network service, no multiple external users. Intended as a portfolio/educational project, not a commercial product.

## 2. Disclaimer and Compliance

**Claude (Anthropic):** local OAuth session only for personal, ordinary use; Claude.ai login; no token extraction/hacking; migrate to official API key if ever serving other users.

**Antigravity (Google):** official auth OAuth session; must comply with Google's Prohibited Use Policy for the underlying **Gemini API**; credentials never shared.

**Allowed authentication matrix:**

| Scenario                    | Claude local OAuth      | Antigravity official method |
| ---------------------------- | ------------------------ | ---------------------------- |
| Personal work on my Mac      | **Allowed — in scope**   | **Allowed — in scope**       |
| Local automation for myself  | Allowed with caution      | Allowed                      |

## 3. Objectives

**Functional:** personal, reproducible workflow using either Claude or Antigravity, selected by config.
**Portfolio:** demonstrate multi-provider architecture, compliance-by-design across two vendors, clear documentation.
**Non-objectives:** not SaaS, no multi-user, no public endpoints, doesn't redistribute either provider.

## 4. Technical Architecture

**Overview:** Terminal/Warp → Provider Router (config-driven) → Claude Code CLI (local OAuth) **or** Antigravity CLI (local OAuth or similar) → shared Config Layer.

**Components:**

| Component              | Status                  |
| ---------------------- | ------------------------ |
| Claude Code CLI         | Implemented              |
| Antigravity Adapter     | Implemented              |
| Provider Router         | Implemented (in scope)   |
| Config Layer            | Implemented              |
| CLAUDE.md per project   | Implemented              |
| Compliance Guard        | Manual + config checks   |

**Stack:** Claude Code CLI, Antigravity official API (backed by **Gemini API**), Warp, PyCharm, YAML/JSON/Markdown config, Git, Python (router implementation).

**Directory structure:**
```
ai-provider-router/
  openspec/PROJECT_SPEC.md
  config/provider.yaml
  router/route.py
  claude/settings.example.json, CLAUDE.md.template
  antigravity/antigravity.env.example, GEMINI.md.template
  docs/README.md, DISCLAIMER.md
  examples/workflow-personal-local-{claude,antigravity}.md
```

**provider.yaml:**
```yaml
default_provider: antigravity
providers:
  claude: { auth_source: local_oauth, scope: personal_only }
  antigravity: { auth_source: local_oauth, scope: personal_only }
routing:
  rules:
    - match: { task_type: coding } -> use_provider: claude
    - match: { task_type: general } -> use_provider: antigravity
```

## 5. Functional Specification

**Actors:** User (me), Claude Code CLI, Antigravity Adapter, Project repository.

**Use cases:**
- UC-01 Start Claude session
- UC-02 Configure Antigravity access
- UC-03 Select provider via config
- UC-04 Work on dev task
- UC-05 Re-auth Claude
- UC-06 Rotate Antigravity key

**Functional requirements:**
- FR-01 The router MUST read `config/provider.yaml` before dispatching a task.
- FR-02 The router MUST support a `default_provider` used when no routing rule matches.
- FR-03 The router MUST support routing rules keyed on `task_type` (or an explicit `--provider` override).
- FR-04 The router MUST dispatch to the Claude Code CLI using the user's existing local OAuth session (no embedded credentials).
- FR-05 The router MUST dispatch to the Antigravity CLI/adapter using the user's existing official auth session (no embedded credentials).
- FR-06 Each target project SHOULD carry a `CLAUDE.md` and/or `GEMINI.md` giving provider-specific context.

**Non-functional requirements:**
- NFR-01 All processing stays local; no proxying through a third-party network service.
- NFR-02 No plaintext secrets committed to the repo (`.env` files are git-ignored; only `.example` templates are tracked).
- NFR-03 Setup must be reproducible from a clean clone (README + example configs).
- NFR-04 The disclaimer must be visible in the repo root README.
- NFR-05 Compliance constraints (personal-use only, no redistribution) are enforced by design and documented, not just asserted.

## 6. Portfolio Roadmap

| Phase | Content                                          | Status      |
| ----- | ------------------------------------------------- | ----------- |
| 1     | Document reference architecture                    | Done        |
| 2     | Implement provider.yaml loader + Router            | In progress |
| 3     | Publish repo with templates for both providers     | Pending     |
| 4     | Architecture diagram + compliance write-up         | Pending     |
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
