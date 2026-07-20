"""Fail-fast startup validation (design.md D6): refuse to serve traffic if a
required provider CLI isn't on PATH. Scope note: this checks presence only —
verifying an active login session would require actually invoking each CLI,
which is left as a "where feasible" future improvement, not implemented here.
"""

import shutil
from collections.abc import Callable


class StartupValidationError(Exception):
    """Raised when a required provider CLI is not available at startup."""


def validate_startup(
    commands: list[str],
    which: Callable[[str], str | None] = shutil.which,
) -> None:
    missing = [cmd for cmd in commands if which(cmd) is None]
    if missing:
        raise StartupValidationError(
            f"Required CLI(s) not found on PATH: {', '.join(missing)}. "
            "Install them and log in before starting the router."
        )
