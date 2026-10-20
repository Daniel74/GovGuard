"""Stage ② of the selection (ARCHITECTURE 1.1): one LLM verdict per requirement (ADR 0007).

Pure logic: gets the Pydantic AI model injected (ADR 0005), no boto3.
"""

import json
import logging
from dataclasses import dataclass

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, SourceName
from kb_build.extract.models import Requirement
from kb_build.llm_step import LlmStep, prompt_version
from kb_build.reference.cfn_types import load_cfn_types
from kb_build.reference.scope import Scope
from kb_build.select.judgement_cache import JudgementCache, cache_key
from kb_build.select.models import Classification
from kb_build.select.prompts import PROMPTS, SCOPE_PROMPT, USER_PROMPT

logger = logging.getLogger("kb_build")

TOOL_NAME = "classify_requirement"
TOOL_DESCRIPTION = "Gib an, ob die Anforderung prüfbar ist."


@dataclass(frozen=True)
class ClassifyDeps:
    """Run dependencies of the agent (ADR 0005): built once per audit type."""

    audit_type: AuditType
    instructions: str
    scope: Scope | None = None  # architecture: types outside it are dropped (#19)
    cfn_types: frozenset[str] = frozenset()  # the real types: the model must not invent any


def build_deps(
    audit_type: AuditType, scope: Scope | None = None, cfn_types: frozenset[str] | None = None
) -> ClassifyDeps:
    """The scope belongs to the architecture prompt only (ADR 0011).

    Without `cfn_types` the architecture audit reads the checked-in list; the spec needs none.
    """
    if cfn_types is None:
        cfn_types = load_cfn_types() if audit_type == "architecture" else frozenset()
    text = PROMPTS[audit_type]
    if audit_type == "architecture" and scope is not None:
        text += "\n" + SCOPE_PROMPT.format(services=", ".join(scope.services))
        return ClassifyDeps(audit_type, text, scope, cfn_types)
    return ClassifyDeps(audit_type, text, cfn_types=cfn_types)


def request_version(deps: ClassifyDeps) -> str:
    """Prompt version of the cache key: instructions, user message, tool definition and the
    scope types the validator keeps. The prompt shows services only; a new type of a known
    service must still mean a full run (#19).
    """
    schema = json.dumps(Classification.model_json_schema(), sort_keys=True)
    scope_types = sorted(deps.scope.types) if deps.scope else []
    return prompt_version(
        deps.instructions, USER_PROMPT, TOOL_NAME, TOOL_DESCRIPTION, schema, *scope_types)


classify_agent = Agent(
    output_type=ToolOutput(Classification, name=TOOL_NAME, description=TOOL_DESCRIPTION),
    deps_type=ClassifyDeps,
    retries=2,  # build only, no 29 s timeout (ADR 0005 limits the runtime agents to one retry)
    model_settings={"temperature": 0},  # same input, same selection (ARCHITECTURE 1.1)
)


@classify_agent.instructions
def _instructions(ctx: RunContext[ClassifyDeps]) -> str:
    return ctx.deps.instructions


@classify_agent.output_validator
def _validate(ctx: RunContext[ClassifyDeps], answer: Classification) -> Classification:
    if ctx.deps.audit_type == "spec":
        return answer.model_copy(update={"cfn_resource_types": [], "scope_level": "template"})
    if not answer.testable:
        return answer.model_copy(update={"cfn_resource_types": []})
    known = ctx.deps.cfn_types
    real = [t for t in answer.cfn_resource_types if t in known]
    invalid = [t for t in answer.cfn_resource_types if t not in known]
    if not real:
        raise ModelRetry(
            "Eine prüfbare Architektur-Anforderung braucht mindestens einen echten "
            f"CloudFormation-Typ (Format AWS::Dienst::Ressource). Diese gibt es nicht: {invalid}"
        )
    if invalid:  # the code drops invented types, no retry needed (#18)
        logger.info("dropped invented resource types: %s", invalid)
    if ctx.deps.scope is not None:  # strip types outside the scope (ADR 0013)
        outside = ctx.deps.scope.outside(real)
        real = [t for t in real if t not in outside]
        if outside:
            logger.info("dropped types outside the scope: %s", outside)
    return answer.model_copy(update={"cfn_resource_types": real})


def classify_requirement(
    requirement: Requirement, source: SourceName, deps: ClassifyDeps, model: Model,
    usage: RunUsage | None = None,
) -> Classification:
    prompt = USER_PROMPT.format(
        source=source, id=requirement.id, title=requirement.title, text=requirement.text)
    return classify_agent.run_sync(prompt, model=model, deps=deps, usage=usage).output


class Judge:
    """Asks the LLM once per requirement; a known answer comes from the cache (ADR 0011).

    An answer that stays invalid after the retries gives `None` (outcome `llm_error`);
    it does not abort the whole run, and it is never cached.
    """

    def __init__(
        self, audit_type: AuditType, model: Model,
        scope: Scope | None = None, cache: JudgementCache | None = None,
    ) -> None:
        self.audit_type, self.model_id = audit_type, model.model_name
        self._model, self._deps = model, build_deps(audit_type, scope)
        self._version = request_version(self._deps)
        self._step = LlmStep(cache if cache is not None else JudgementCache())
        self._answers: dict[tuple[SourceName, str], Classification | None] = {}
        self.usage = self._step.usage  # tokens of the calls the cache could not answer
        self.counts = self._step.counts  # retries and llm_error of those calls (#27)

    def __call__(self, source: SourceName, requirement: Requirement) -> Classification | None:
        key = (source, requirement.id)
        if key not in self._answers:
            cached = cache_key(requirement, self._version, self.model_id)
            self._answers[key] = self._step.cached_or_ask(
                cached, lambda: self._ask(source, requirement))
        return self._answers[key]

    def _ask(self, source: SourceName, requirement: Requirement) -> Classification | None:
        return self._step.ask(
            f"{self.audit_type} {source} {requirement.id}",
            lambda usage: classify_requirement(requirement, source, self._deps, self._model, usage),
            "%s %s: invalid answer after retries: %s", source, requirement.id)
