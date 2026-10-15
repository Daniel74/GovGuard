"""Stage 5 over the whole selection (ARCHITECTURE 1): one rule each, then the gate.

Pure logic: gets the Pydantic AI model injected, no boto3. One rule is formulate.py's task.
"""

import logging

from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, RuleCatalog
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


def formulate_rules(
    model: Model, selection: Selection, sources: list[ExtractedSource],
    properties: PropertyIndex, scope: Scope,
) -> RuleCatalog:
    """One rule per selected requirement, in selection order; then the gate (ARCHITECTURE 1)."""
    anchors = requirements_by_anchor(sources)
    by_id = {(s.source, r.id): r for s in sources for r in s.requirements}
    rules, started, usage = [], [], RunUsage()
    try:
        for n, selected in enumerate(selection.selected, start=1):
            requirement = by_id[(selected.source, selected.requirement_id)]
            started.append(FormulateDeps(selection.audit_type, selected, requirement, anchors,
                                         properties, scope))
            rules.append(complete_rule(started[-1], model, usage))
            logger.info("%s %d/%d %s", selection.audit_type, n, len(selection.selected),
                        rules[-1].id)
    finally:  # an llm_error aborts the build; the quality report still counts it
        logger.info(usage_line(selection.audit_type, usage))
        _log_quality(selection.audit_type, started)
    used = {s.source for s in selection.selected}
    catalog = RuleCatalog(
        audit_type=selection.audit_type, model_id=model.model_name, rules=rules,
        source_versions={s.source: s.version for s in sources if s.source in used},
    )
    check_rules(catalog, selection, sources, scope)
    return catalog
