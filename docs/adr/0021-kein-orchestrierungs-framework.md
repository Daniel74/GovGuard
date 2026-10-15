# 0021 – Kein Orchestrierungs-Framework (LangChain/LangGraph)

_Bestätigt [ADR 0005](0005-pydantic-ai.md). Anlass: mit dem FAIL-Prüfer (#31) gibt es zur Laufzeit drei LLM-Schritte._

## Kontext

- Laufzeit: Architektur-Audit Inventar → Prüfpakete parallel, Spec-Audit Prüfpakete parallel → FAIL-Prüfer. Jeder Schritt ist ein Pydantic-AI-`Agent` mit genau einem strukturierten Aufruf, Validator und höchstens einem Retry. Die Reihenfolge steht fest, kein LLM entscheidet den nächsten Schritt.
- Die Orchestrierung sind ca. 40 Zeilen `asyncio` (`gather` + `Semaphore`) in `audit_engine.py`. Lambda ist zustandslos und hat 180 s (ADR 0018).
- LangGraph (Abläufe als Graph mit Zustand) hilft bei Zyklen, Verzweigungen durch das LLM, Checkpoints und Mensch in der Schleife. Nichts davon kommt bei GovGuard vor.

## Entscheidung

- Kein LangChain, kein LangGraph. Die Pipeline bleibt Python-Code mit `asyncio`, jeder LLM-Schritt ein Pydantic-AI-`Agent`.
- Ein neuer Prüfer ist ein neuer `Agent` plus ein Funktionsaufruf in der Pipeline.
- Braucht ein Ausbau echte Zyklen, prüfen wir zuerst `pydantic-graph` aus demselben Ökosystem.

## Konsequenzen

- `output_validator` + `ModelRetry` (Code prüft, LLM korrigiert, ADR 0017) und die Retry-Gründe aus `capture_run_messages` (#30) bleiben. Mit LangChain müssten wir sie als Graph-Zyklus nachbauen.
- Lambda-Paket bleibt schlank (`pydantic-ai-slim`); Tests bleiben bei `FunctionModel`/`TestModel` (14 Testdateien).
- Kein Graph-Bild und kein LangSmith-Tracing aus dem Framework; den Ablauf zeigt `docs/ARCHITECTURE.md`. Migration geschätzt 3–4 Arbeitstage, vor der Präsentation am 26.10.2026 nicht vertretbar.

## Fachgespräch-Satz

„Meine Prüfer bilden eine feste Pipeline, keinen Agenten-Graphen: Dafür reicht `asyncio`, und das Framework übernimmt nur, was mir echt Arbeit spart – Schema, Validierung und Retry.“
