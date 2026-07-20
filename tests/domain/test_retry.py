import pytest

from router.domain.retry import retry_on_predicate


async def test_returns_first_result_when_predicate_is_false():
    calls = []

    async def fn():
        calls.append(1)
        return "ok"

    result = await retry_on_predicate(fn, should_retry=lambda r: False, max_attempts=3)

    assert result == "ok"
    assert len(calls) == 1


async def test_retries_until_predicate_is_false():
    calls = []

    async def fn():
        calls.append(1)
        return "empty" if len(calls) == 1 else "ok"

    result = await retry_on_predicate(fn, should_retry=lambda r: r == "empty", max_attempts=3)

    assert result == "ok"
    assert len(calls) == 2


async def test_returns_last_result_when_attempts_exhausted():
    calls = []

    async def fn():
        calls.append(1)
        return "empty"

    result = await retry_on_predicate(fn, should_retry=lambda r: r == "empty", max_attempts=2)

    assert result == "empty"
    assert len(calls) == 2


async def test_max_attempts_of_one_never_retries():
    calls = []

    async def fn():
        calls.append(1)
        return "empty"

    result = await retry_on_predicate(fn, should_retry=lambda r: r == "empty", max_attempts=1)

    assert result == "empty"
    assert len(calls) == 1
