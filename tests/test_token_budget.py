"""Token budget per minute for Groq (#53): 37 packages of an 84 KB input broke the tier limit."""

import asyncio

from govguard.token_budget import TokenBudget, estimated_tokens


class FakeTime:
    """Clock and sleep without waiting: sleep moves the clock."""

    def __init__(self) -> None:
        self.now, self.slept = 0.0, []

    def clock(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def take_all(budget: TokenBudget, *requests: int) -> None:
    async def run() -> None:
        for tokens in requests:
            await budget.take(tokens)

    asyncio.run(run())


def test_requests_within_the_minute_budget_do_not_wait() -> None:
    time = FakeTime()
    take_all(TokenBudget(100, time.clock, time.sleep), 40, 60)
    assert time.slept == []


def test_a_request_over_the_budget_waits_until_the_oldest_leaves_the_minute() -> None:
    time = FakeTime()
    budget = TokenBudget(100, time.clock, time.sleep)
    take_all(budget, 60)
    time.now = 10.0

    take_all(budget, 60)

    assert time.slept == [50.0]  # the first 60 tokens count until second 60


def test_a_request_bigger_than_the_budget_goes_alone() -> None:
    time = FakeTime()
    take_all(TokenBudget(100, time.clock, time.sleep), 150)
    assert time.slept == []


def test_the_estimate_counts_the_prompt_and_reserves_the_whole_answer() -> None:
    # Groq counts max_tokens against the minute (x-ratelimit-remaining-tokens, 19.10.2026)
    assert estimated_tokens("x" * 30_000, 8_000) == 10_000 + 8_000
