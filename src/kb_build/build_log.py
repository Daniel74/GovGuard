"""Build log of an agent run: each retry and the rejected last answer with its reason (#30).

A line names whose answer went back (the label) and which gate sent it back:
`schema` (Pydantic AI checks the answer format), `code` (the validator) or `judge`.
The reason is what the model reads (CONTEXT.md: Korrektur), in one line: the validator's text,
or field and message of each schema error, without the JSON wrapping.
"""

import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from pydantic import ValidationError
from pydantic_ai import ModelRetry, UnexpectedModelBehavior
from pydantic_ai.agent import capture_run_messages
from pydantic_ai.messages import RetryPromptPart
from pydantic_core import ErrorDetails

logger = logging.getLogger("kb_build")
NOTE = "build log: "  # marks a rejection a nested run has logged already


def code_gate(reason: str) -> str:
    return "code"


@contextmanager
def logged_retries(label: str, gate_of: Callable[[str], str] = code_gate) -> Iterator[None]:
    """Logs after the agent run inside: its messages hold every retry, schema errors included.

    `gate_of` names the gate of a validator text. An aborted run adds the reason of its last
    answer: no retry, but it explains the abort. A nested run (the judge) logs its own abort.
    """
    rejected = None
    with capture_run_messages() as messages:
        try:
            yield
        except UnexpectedModelBehavior as error:
            rejected = _rejection(error.__cause__, label, gate_of)
            raise
        finally:
            parts = [p for m in messages for p in m.parts if isinstance(p, RetryPromptPart)]
            for n, part in enumerate(parts, start=1):
                logger.info("%s retry %d %s", label, n, _line(part, gate_of))
            if rejected is not None:
                logger.info("%s rejected %s", label, rejected)


def _line(part: RetryPromptPart, gate_of: Callable[[str], str]) -> str:
    if isinstance(part.content, str) and part.tool_name is not None:  # the validator's text
        return f"({gate_of(part.content)}): {_reason(part.content)}"
    return f"(schema): {_reason(part.content)}"  # a format error, or no tool call at all


def _rejection(
    cause: BaseException | None, label: str, gate_of: Callable[[str], str]
) -> str | None:
    """Pydantic AI keeps the last rejection as the cause of its retry limit error.

    The note on it keeps an outer run from logging the judge's rejection as its own;
    the traceback shows it too.
    """
    if cause is None or any(n.startswith(NOTE) for n in getattr(cause, "__notes__", [])):
        return None
    if isinstance(cause, ModelRetry):
        rejected = f"({gate_of(cause.message)}): {_reason(cause.message)}"
    elif isinstance(cause, ValidationError):
        rejected = f"(schema): {_reason(cause.errors())}"
    else:
        return None
    cause.add_note(f"{NOTE}{label} rejected {rejected}")
    return rejected


def _reason(content: str | list[ErrorDetails]) -> str:
    if isinstance(content, str):
        return " ".join(content.split())  # one line per retry
    return "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in content)
