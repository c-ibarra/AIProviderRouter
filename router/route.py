#!/usr/bin/env python3
"""Config-driven dispatcher: picks Claude or Antigravity per config/provider.yaml
and execs into that provider's local CLI with the remaining arguments."""

import argparse
import os
import sys
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "provider.yaml"


def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def resolve_provider(config: dict, task_type: str | None, override: str | None) -> str:
    if override:
        return override
    if task_type:
        for rule in config.get("routing", {}).get("rules", []):
            if rule.get("match", {}).get("task_type") == task_type:
                return rule["use_provider"]
    return config["default_provider"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Route a task to Claude or Antigravity based on config/provider.yaml"
    )
    parser.add_argument("--task-type", help="e.g. coding, general — matched against routing.rules")
    parser.add_argument("--provider", help="explicit override: claude | antigravity")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="arguments passed through to the provider CLI")
    parsed = parser.parse_args()

    config = load_config(CONFIG_PATH)
    provider = resolve_provider(config, parsed.task_type, parsed.provider)

    provider_config = config["providers"].get(provider)
    if provider_config is None:
        print(f"Unknown provider '{provider}' — check config/provider.yaml", file=sys.stderr)
        return 1

    cli_command = provider_config["cli_command"]
    print(f"[ai-provider-router] dispatching to '{provider}' ({cli_command})", file=sys.stderr)

    try:
        os.execvp(cli_command, [cli_command, *parsed.args])
    except FileNotFoundError:
        print(f"'{cli_command}' not found on PATH — is the {provider} CLI installed?", file=sys.stderr)
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
