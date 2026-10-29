"""What the box under a site shows first and what it folds away (#86): WARN and FAIL as one-liners
(FAIL first), the rest behind a fold row. The component only draws; the split, the order and the
text of the fold row are prepared here. Pure view logic, no Streamlit."""

from govguard.checks.remediation import open_findings
from govguard.checks.sites import Site
from govguard.models import Finding

NO_NEED = {"PASS": "erfüllt", "N/A": "nicht anwendbar"}  # status -> word in the fold row text


def to_act_on(site: Site) -> list[Finding]:
    """WARN and FAIL of the site, FAIL first, on equal status the order of lines."""
    return sorted(open_findings(site), key=lambda f: f.status != "FAIL")


def without_need(site: Site) -> list[Finding]:
    """Everything that is not open (PASS, N/A) in the order of lines: nothing to do, folded away.
    Defined as the rest, so that no finding can fall out of the box."""
    acting = {f.rule_id for f in open_findings(site)}
    return [f for f in site.findings if f.rule_id not in acting]


def first_to_look_at(site: Site) -> Finding:
    """What a click on the bar or a line chooses: the first thing to act on, since a PASS would
    open the box on a folded finding. Without WARN/FAIL: the first by lines."""
    return (to_act_on(site) or site.findings)[0]


def rest_text(rest: list[Finding]) -> str:
    """Text of the fold row, e.g. "3 ohne Handlungsbedarf (2 erfüllt, 1 nicht anwendbar)"."""
    parts = [f"{n} {word}" for status, word in NO_NEED.items()
             if (n := sum(f.status == status for f in rest))]
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"{len(rest)} ohne Handlungsbedarf{detail}" if rest else ""


def under_measures(site: Site, measures: list[dict]) -> tuple[dict[str, list[str]], list[str]]:
    """Measure id -> the visible WARN/FAIL it covers (FAIL first), and the visible ones no measure
    names (a check of the proposal should rule that out; the box keeps them, none may get lost).
    measures: the dicts of remediation_data (`id`, `rule_ids`). A finding stands under the first
    measure that names it. The proposal covers the unfiltered site, `site` is the filtered one."""
    if not measures:  # no proposal: the findings stand under "Befunde"
        return {}, []
    acting = [f.rule_id for f in to_act_on(site)]
    taken: set[str] = set()
    grouped = {}
    for measure in measures:
        grouped[measure["id"]] = [i for i in acting if i in measure["rule_ids"] and i not in taken]
        taken.update(grouped[measure["id"]])
    named = {i for measure in measures for i in measure["rule_ids"]}
    return grouped, [i for i in acting if i not in named]


def box_parts(site: Site, selected: str, measures: list[dict] | None = None) -> dict:
    """ids in the order of the box. The fold row opens by itself when it holds the selected one.
    measures: those of a proposal; then the box lists the findings under them (by_measure, and
    leftover for the ones no measure names), else under the heading "Befunde" (open)."""
    rest = without_need(site)
    grouped, leftover = under_measures(site, measures or [])
    return {"open": [f.rule_id for f in to_act_on(site)], "rest": [f.rule_id for f in rest],
            "rest_text": rest_text(rest), "by_measure": grouped, "leftover": leftover,
            "rest_auto": selected in [f.rule_id for f in rest]}
