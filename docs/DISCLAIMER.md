# Disclaimer

Educational/study project. Not affiliated with or endorsed by Anthropic or Google. Use at your own risk.

`ai-provider-router` uses:

- **Claude Code**, via the official `claude-agent-sdk`, authenticated through the author's own local OAuth session (`claude login`). No API key is stored or requested by this project.
- **Antigravity**, via the official `agy` CLI's headless mode, authenticated through the author's own local OAuth session (`agy login`). No API key is stored or requested by this project. See `docs/adr/0001-antigravity-cli-over-sdk.md` for why this project deliberately avoids both the official SDK's API-key auth path and any unofficial OAuth-bridging tool.

Provider selection happens via local configuration (`config/provider.yaml`), not by proxying, redistributing, or reselling either provider's service.

This project:

- Runs entirely locally. It is not a network service — the HTTP endpoint it exposes binds to `127.0.0.1` only and is never reachable from outside the machine it runs on.
- Does not proxy traffic to or from any third party.
- Does not share, transmit, or expose either provider's credentials to any other process or service.
- Is intended for personal, single-user use by its author — not for serving other users, and not for commercial use. See `openspec/PROJECT_SPEC.md` §2–3 for the full compliance posture and the allowed-use matrix.

Follows Anthropic's terms of service for Claude Code and Google's Prohibited Use Policy for the Gemini API (which Antigravity is built on). If this project were ever adapted to serve other users, it would need to migrate off personal OAuth sessions onto officially provisioned, per-user API credentials first — that is explicitly out of scope for this project as it exists today.
