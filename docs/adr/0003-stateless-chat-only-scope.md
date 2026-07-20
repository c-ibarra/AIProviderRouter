# Stateless, tool-free (chat-only) scope for v1

Both `claude-agent-sdk` and the `agy` CLI are agentic by default — they can read/edit files and run shell commands in whatever working directory they're given, and both support server-side multi-turn session resume (`resume=` for Claude, `--conversation`/`-c` for Antigravity). The router deliberately uses neither capability in v1: all file/command tools are disabled (`policy.deny_all()` equivalent on the Antigravity leg, `--disallowedTools` on the Claude leg), and the router keeps no session store — every request forwards the caller's full message history (which Warp already sends, per the OpenAI chat-completions contract) as a fresh transcript, rather than mapping conversations to a provider-side session ID.

**Why:**

- **Tool-free:** exposing agentic file/command tools behind a chat endpoint means every message from Warp could trigger real file edits or shell execution with no human present to answer a tool-confirmation prompt (`ask_user` policies have no UI to render into over a chat API). Disabling tools sidesteps designing a headless confirmation policy entirely, at the cost of losing the agentic capability that's the whole point of Claude Code / Antigravity when used directly — an acceptable v1 trade-off since both tools remain available directly for actual agentic work.
- **Stateless:** Claude's `resume=` needs the router to track a session ID per conversation (a session store, correlation logic against Warp's opaque conversation identity). Antigravity's equivalent mechanism has a documented gap (ADR-0001): no way to capture/assign a conversation ID from a `--print` run. Rather than build session-tracking infrastructure for Claude alone and route around a permanent gap for Antigravity, the router treats both legs identically: forward the full history every time. This trades reprocessing cost on long conversations for zero session-management code and no asymmetry between the two provider legs on this axis.

## Consequences

Both are easy to revisit independently later (enable tools with an explicit auto-allow policy scoped to a fixed workspace; add a session store once real usage shows reprocessing cost matters) without changing the `ProviderPort` shape from ADR-0002.
