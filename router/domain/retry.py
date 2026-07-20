"""Generic retry-on-predicate helper, used by AntigravityAdapter for the
known agy -p "exit 0, empty stdout" failure mode (ADR-0001, design.md D4)."""

from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_on_predicate(
    fn: Callable[[], Awaitable[T]],
    should_retry: Callable[[T], bool],
    max_attempts: int,
) -> T:
    """Call `fn` up to `max_attempts` times, retrying while `should_retry(result)` is True.

    Returns the last result once `should_retry` is False or attempts are exhausted.
    """
    result = await fn()
    attempts = 1
    while should_retry(result) and attempts < max_attempts:
        result = await fn()
        attempts += 1
    return result
