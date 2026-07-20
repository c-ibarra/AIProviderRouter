"""AntigravityAdapter: ProviderPort backed by the `agy` CLI's headless -p mode
(ADR-0001), invoked as a subprocess. Stateless, single-chunk (ADR-0003)."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from router.domain.errors import ProviderError
from router.domain.port import ProviderConfig, ProviderPort, ProviderResponse
from router.domain.retry import retry_on_predicate
from router.domain.transcript import Transcript


@dataclass
class SubprocessResult:
    exit_code: int
    stdout: str
    stderr: str


async def _default_run_subprocess(args: list[str]) -> SubprocessResult:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return SubprocessResult(
        exit_code=process.returncode,
        stdout=stdout.decode(),
        stderr=stderr.decode(),
    )


def _is_empty_output(result: SubprocessResult) -> bool:
    return result.exit_code == 0 and result.stdout.strip() == ""


class AntigravityAdapter(ProviderPort):
    def __init__(
        self,
        cli_command: str = "agy",
        run_subprocess: Callable[[list[str]], Awaitable[SubprocessResult]] | None = None,
        retry_max_attempts: int = 2,
        retry_on_empty_output: bool = True,
    ):
        self._cli_command = cli_command
        self._run_subprocess = run_subprocess or _default_run_subprocess
        self._retry_max_attempts = retry_max_attempts
        self._retry_on_empty_output = retry_on_empty_output

    async def send(self, transcript: Transcript, config: ProviderConfig) -> ProviderResponse:
        args = [self._cli_command, "-p", transcript.flatten(), "--model", config.model]

        should_retry = _is_empty_output if self._retry_on_empty_output else (lambda _: False)
        result = await retry_on_predicate(
            fn=lambda: self._run_subprocess(args),
            should_retry=should_retry,
            max_attempts=self._retry_max_attempts,
        )

        if self._retry_on_empty_output and _is_empty_output(result):
            raise ProviderError(
                f"agy -p returned exit 0 with empty stdout after "
                f"{self._retry_max_attempts} attempt(s)"
            )

        return ProviderResponse(text=result.stdout, stream=None)
