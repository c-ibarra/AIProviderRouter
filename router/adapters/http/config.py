"""provider.yaml loader. Called fresh on every request (design.md D5) — no
process-level caching, so editing default_provider takes effect immediately."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ProviderSettings:
    auth_source: str
    scope: str
    model: str
    effort: str | None = None
    retry_max_attempts: int = 2
    retry_on_empty_output: bool = True


@dataclass
class RouterConfig:
    default_provider: str
    providers: dict[str, ProviderSettings]


def load_config(path: Path) -> RouterConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    providers = {}
    for name, settings in raw["providers"].items():
        retry = settings.get("retry", {})
        providers[name] = ProviderSettings(
            auth_source=settings["auth_source"],
            scope=settings["scope"],
            model=settings["model"],
            effort=settings.get("effort"),
            retry_max_attempts=retry.get("max_attempts", 2),
            retry_on_empty_output=retry.get("on_empty_output", True),
        )

    return RouterConfig(default_provider=raw["default_provider"], providers=providers)
