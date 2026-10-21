"""Token budget per minute for Groq (#53). Pure logic; clock and sleep are injected for tests.

Groq's tier allows 250,000 tokens per minute (header x-ratelimit-limit-tokens) and counts the
prompt plus the whole max_tokens of the answer. Two parallel packages of an 84 KB input broke
it (spec-wohngeld-openapi, 367 rules): the audit failed after 136 s.
"""

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable

GROQ_TOKENS_PER_MINUTE = 200_000  # margin to 250,000 for retries and the fail judge
CHARS_PER_TOKEN = 3  # measured ~3.4 for numbered German text and JSON; lower is safer
WINDOW_S = 60.0


def estimated_tokens(prompt: str, max_output: int) -> int:
    """What Groq counts against the minute: the prompt and the reserved answer."""
    return len(prompt) // CHARS_PER_TOKEN + max_output


class TokenBudget:
    """Sliding minute: a request waits until the tokens of the last 60 s leave room for it."""

    def __init__(
        self, per_minute: int, clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._per_minute, self._clock, self._sleep = per_minute, clock, sleep
        self._spent: deque[tuple[float, int]] = deque()  # (time, tokens) of the last minute

    async def take(self, tokens: int) -> None:
        """No await between check and booking: packages of one event loop cannot overtake."""
        while True:
            now = self._clock()
            while self._spent and self._spent[0][0] <= now - WINDOW_S:
                self._spent.popleft()
            used = sum(spent for _, spent in self._spent)
            if not self._spent or used + tokens <= self._per_minute:  # too big: goes alone
                self._spent.append((now, tokens))
                return
            await self._sleep(self._spent[0][0] + WINDOW_S - now)
