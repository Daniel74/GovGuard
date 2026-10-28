"""Test app of tests/visual, never part of the demo: the whole UI with a fake model call and a
fixed password, so the browser can click through "Maßnahme vorschlagen" without Groq (#82).

src/ has no test hook: the suggest_url fixture starts this and it swaps the model call.
"""

from govguard.checks.remediation_models import Measure
from govguard.checks.sites import Site
from govguard_ui.app import main
from govguard_ui.screens import measure_runner

PASSWORD = "vorschlag"
CODE = "  Zeile vorher\n  zweite Zeile"


async def fake_measures(site: Site, document: str, model: object) -> list[Measure]:
    first = site.findings[0]
    return [Measure(sentence="Bucket-Ziel eintragen.", before=CODE, after="  Zeile [Bucket-ARN]",
                    line_start=first.line_start, line_end=first.last_line,
                    rule_ids=[f.rule_id for f in site.findings],
                    anchors=[first.primary_anchor, "CIS AWS v7.0.0 3.1.4"])]


if __name__ == "__main__":  # Streamlit runs a script as __main__; the test imports PASSWORD only
    # a local .streamlit/secrets.toml would win over an environment variable
    measure_runner.secret = {"APP_PASSWORD": PASSWORD}.get
    measure_runner.groq_model = lambda: None
    measure_runner.suggest_measures = fake_measures
    main()
