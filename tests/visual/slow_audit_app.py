"""Test app of tests/visual, never part of the demo: the whole UI with an audit that takes a few
seconds and needs no Groq, time enough to click a page link while it runs (#77).

src/ has no test hook: the slow_url fixture starts this and it swaps the model call.
"""

import time

from govguard.models import AuditReport, Progress
from govguard_ui.app import main
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.screens import create_page

PASSWORD = "langsam"
PACKAGES = 8  # one second each


def slow_audit(_audit_type, _text, _model, on_progress) -> AuditReport:
    for done in range(PACKAGES):  # a page switch stops the run here, in the progress call
        on_progress(Progress(phase="packages", packages_done=done, packages_total=PACKAGES))
        time.sleep(1)
    return load_gallery(PRESETS, GALLERY)[0].report


if __name__ == "__main__":  # Streamlit runs a script as __main__; the test imports PASSWORD only
    # a local .streamlit/secrets.toml would win over an environment variable
    create_page.secret = {"APP_PASSWORD": PASSWORD}.get
    create_page.groq_model = lambda: None
    create_page.run_local = slow_audit
    main()
