"""Transcript: internal representation of an OpenAI messages[] array.

Built once per request from the caller's full message history (ADR-0003:
stateless — no session store, every request is a fresh transcript).
"""

from dataclasses import dataclass, field


@dataclass
class Turn:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class Transcript:
    system: str | None
    turns: list[Turn] = field(default_factory=list)

    @classmethod
    def from_messages(cls, messages: list[dict]) -> "Transcript":
        system = None
        turns = []
        for message in messages:
            if message["role"] == "system":
                system = message["content"]
            else:
                turns.append(Turn(role=message["role"], content=message["content"]))
        return cls(system=system, turns=turns)

    def flatten(self) -> str:
        """Flatten into a single string for backends with no structured input (agy -p)."""
        lines = []
        if self.system is not None:
            lines.append(f"System: {self.system}\n")
        lines.extend(f"{turn.role.capitalize()}: {turn.content}" for turn in self.turns)
        return "\n".join(lines)

    def flatten_turns_only(self) -> str:
        """Flatten just the turns, excluding the system message.

        Used for Claude, whose SDK accepts the system prompt as a separate
        parameter (ClaudeAgentOptions.system_prompt) rather than inline text.
        """
        return "\n".join(f"{turn.role.capitalize()}: {turn.content}" for turn in self.turns)
