"""Stage 5 over the whole selection (ARCHITECTURE 1): one rule each, then the gate.

Pure logic: gets the Pydantic AI model injected, no boto3. One rule is formulate.py's task.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, Rule, RuleCatalog
from kb_build.extract.models import ExtractedSource
from kb_build.gates import GateCounts, check_rules, requirements_by_anchor, usage_line
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.reference.scope import Scope
from kb_build.rules.formulate import FormulateDeps, complete_rule
from kb_build.select.models import Selection

logger = logging.getLogger("kb_build")


def _log_quality(audit_type: AuditType, started: list[FormulateDeps]) -> None:
    """Quality report of the run: each rule counted its own retries, here they add up."""
    logger.info(sum((d.counts for d in started), GateCounts()).line(audit_type, "formulate"))
    if audit_type == "spec":  # architecture rules are never judged
        judge = sum((d.judge_counts for d in started), GateCounts())
        logger.info(judge.line(audit_type, "judge"))


@dataclass(frozen=True)
class RuleInputs:
    """What every rule is checked against; the same for a whole run."""

    sources: list[ExtractedSource]  # every source, for anchors, quotes and cross references
    properties: PropertyIndex
    scope: Scope


def formulate_rules(
    model: Model, selection: Selection, inputs: RuleInputs,
    on_rule: Callable[[Rule], None] | None = None,
) -> RuleCatalog:
    """One rule per selected requirement, in selection order; then the gate (ARCHITECTURE 1).

    A rule that stays invalid does not stop the others: the build aborts at the end and names
    every failed rule (#53). `on_rule` gets each valid rule at once, e.g. for a checkpoint.
    """
    sources, properties, scope = inputs.sources, inputs.properties, inputs.scope
    anchors = requirements_by_anchor(sources)
    by_id = {(s.source, r.id): r for s in sources for r in s.requirements}
    rules, started, failed, usage = [], [], [], RunUsage()
    try:
        for n, selected in enumerate(selection.selected, start=1):
            requirement = by_id[(selected.source, selected.requirement_id)]
            started.append(FormulateDeps(selection.audit_type, selected, requirement, anchors,
                                         properties, scope))
            try:
                rules.append(complete_rule(started[-1], model, usage))
            except ValueError as error:  # an llm_error: the quality report counts it
                failed.append(str(error))
                continue
            if on_rule is not None:
                on_rule(rules[-1])
            logger.info("%s %d/%d %s", selection.audit_type, n, len(selection.selected),
                        rules[-1].id)
    finally:  # the quality report counts an aborted run too
        logger.info(usage_line(selection.audit_type, usage))
        _log_quality(selection.audit_type, started)
    if failed:  # fail closed: no rule may silently go missing
        raise ValueError(f"{len(failed)} rules failed:\n" + "\n".join(failed))
    used = {s.source for s in selection.selected}
    catalog = RuleCatalog(
        audit_type=selection.audit_type, model_id=model.model_name, rules=rules,
        source_versions={s.source: s.version for s in sources if s.source in used},
    )
    check_rules(catalog, selection, sources, scope)
    return catalog
