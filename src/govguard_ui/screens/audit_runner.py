"""Audit erstellen in the demo: Streamlit runs run_audit itself with Groq (ADR 0023)."""

from pathlib import Path

from pydantic_ai.models import Model

from govguard.audit_engine import InputTooLongError, OnProgress, check_input_length, run_audit
from govguard.audit_setup import CATALOGS, conditions_for, make_trace
from govguard.models import AuditReport, AuditType, Progress, RuleCatalog
from govguard_ui.screens.password_gate import configured, password_problem
from govguard_ui.style import JUDGE_NAME


def start_problem(
    text: str, password: str, secret: str | None, confirmed: bool = False,
) -> str | None:
    """Why the audit must not start, or None. Checked before any LLM call: no cost.
    confirmed: the session gave the right password before (also for a measure, #82)."""
    if not configured(secret):  # fail closed: no configured password, no audit
        return "Audit erstellen ist nicht eingerichtet: Das Passwort fehlt in den Secrets."
    if not text.strip():
        return "Die Eingabe ist leer. Bitte einen Text einfügen oder einen Musterfall wählen."
    try:
        check_input_length(text)
    except InputTooLongError as error:
        return str(error)
    if not confirmed and password_problem(password, secret):
        return "Passwort falsch. Ohne Passwort startet kein Audit."
    return None


def backend_problem(backend: str | None) -> str | None:
    """Demo: the audit runs in the Streamlit process (AUDIT_BACKEND=local, ADR 0023)."""
    if backend in (None, "", "local"):
        return None
    if backend == "lambda":
        return "AUDIT_BACKEND=lambda gehört zum Recruiter-Stand (#38) und ist noch nicht gebaut."
    return f"AUDIT_BACKEND={backend} ist unbekannt; erlaubt ist local."


def run_local(
    audit_type: AuditType, text: str, model: Model, on_progress: OnProgress,
    catalog_file: Path | None = None,
) -> AuditReport:
    """Same catalog, trace and engine as the CLI; raises like run_audit (fail closed)."""
    catalog_file = catalog_file or CATALOGS[audit_type]
    catalog_bytes = catalog_file.read_bytes()
    return run_audit(RuleCatalog.model_validate_json(catalog_bytes), text, model,
                     make_trace(text, catalog_bytes), on_progress=on_progress,
                     conditions=conditions_for(audit_type))


def progress_view(progress: Progress) -> tuple[float, str]:
    """Bar fraction and label; the packages fill 90 %, the FAIL judge the rest."""
    if progress.phase == "conditions":
        return 0.0, "Bedingungen der Spezifikation feststellen …"
    if progress.phase == "inventory":
        return 0.0, "Ressourcen erkennen (KI-Vorlauf oder Template) …"
    if progress.phase == "fail_judge":
        return 0.95, f"{JUDGE_NAME} prüft jeden Verstoß nach …"
    if not progress.packages_total:  # every rule N/A by code, nothing goes to the model
        return 0.9, "Alle Prüfregeln vom Code entschieden"
    done = progress.packages_done / progress.packages_total
    return 0.9 * done, f"Paket {progress.packages_done} von {progress.packages_total} geprüft"
