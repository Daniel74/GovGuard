# 99 – Offen, Grenzen und veraltete Stellen

## Was noch nicht gebaut ist (nicht als Gebautes beschreiben)

- **Preset-Gate und `build-kb.yml` (#8, Fahrplan Schritt 11):** Der Build läuft heute lokal, Befehl für Befehl. Geplant: ein Befehl `python -m kb_build` für alles, das Preset-Gate (Gesamtstatus, Pflicht-Befunde, Hash-Check) und ein manueller GitHub-Actions-Workflow, der nur bei Grün einen Pull Request öffnet. Anmeldung per OIDC statt langlebigem Schlüssel; `GROQ_API_KEY` als Secret; die Rolle braucht Bedrock `eu.` nur für das Preset-Gate (ADR 0014).
- **Golden Archetypes (#7, Priorität B, `cdk_runner.py`):** Schleife aus CDK-Generierung, `cdk synth`, Audit und cdk-nag, höchstens 3 Runden. Nur wenn nach Abschluss der Priorität A mindestens 3 Arbeitstage bleiben (Stichtag 16.10.2026).
- **Audit-Engine mit Ressourceninventar (#14), Stack und Endpunkte (#9), Deploy und UI (#11):** gehören zur Laufzeit, nicht zu `kb_build`.

## Bekannte Grenzen der Pipeline

- **Stufe ② urteilt per LLM und nicht stabil** (41 von 1.077 Urteilen gekippt; rund 10 % Auswahlwechsel bei Neulauf). Schutz: Cache und Gates. Einzelne Fehlurteile sind möglich (C5 CRY-07.01B).
- **Nachwürfeln im Lauf von #19:** Zwei Cache-Einträge (CIS 3.1.4, BSI BER.4.1) wurden von Hand gelöscht und neu beurteilt, bis das Gate grün war. Das ist nicht reproduzierbar; die Pflichtanker-Gates bleiben die Absicherung.
- **Fehlende Urteile (`llm_error`):** Je nach Lauf endeten andere Anforderungen ohne Urteil (z. B. FSBP S3.1, BSI BER.6.2, C5 OPS-19.01B). Im aktuellen `verdicts_arch.json` sind es 2 Einträge (BSI BER.6.4, CIS 2.14). Der Lauf geht trotzdem weiter, die Anforderung fehlt im Katalog und steht im Protokoll.
- **Spec-Grenze Vorhaben/Betrieb** (v. a. SDM Ebene P): nicht stabil klassifizierbar; im Zweifel wird aufgenommen. Einige SDM-Prozess-Maßnahmen schießen über (z. B. M50.P05, M51.P28).
- **Uneinheitliches Protokoll:** Konto-/Personenpflichten teils `not_testable` mit LLM-Text statt `not_relevant` mit festem Satz.
- **SDM ohne Protokollieren (M43)**, **DSGVO-Einheit Artikel** (Art. 5), **CIS aus zweiter Hand** (Prowler), **keine kontoweiten Pflichten** (ADR 0007), **Prüfumfang bewusst begrenzt** (kein EC2, EKS, CloudTrail, CloudFront, Classic LB; `docs/AUSBAU.md`).
- **Eigenschafts-Gate mit Heuristik:** Einzelwörter werden nicht geprüft; Qualitätsbericht zählt, was nicht prüfbar ist.
- **Datenschutz im Build:** Groq (US) und ggf. Bedrock `global.` sehen öffentliche Normtexte, auch lizenzierte CIS-Volltexte.

## Stellen in anderen Dokumenten, die dem Code widersprechen (Code gilt)

Beim Ausformulieren **nicht** aus diesen Stellen übernehmen:

FAHRPLAN, Issue-Status und `CLAUDE.md` sind auf dem Stand des Codes. Die folgenden Stellen sind veraltet; das Ticket #22 (Schritt 9f im Fahrplan) zieht sie nach, und #16 übernimmt README und die Erklär-Dokumente.

- `docs/ARCHITECTURE.md` (Fassung vor #64) 1.1: „Relevanz: erster `cfn_resource_type` im Prüfumfang“ gilt seit ADR 0013 nicht mehr; heute genügt ein nach dem Streichen übrig gebliebener Typ im Prüfumfang plus Ebene `template`. 1.3: „zwei Wiederholungen“ beim Formulieren; heute bis zu 6 (`FORMULATE_RETRIES`, ADR 0014). Mit #64 neu geschrieben; die Details stehen heute in DESIGN 1.2 und 2.6.
- `docs/adr/0002`, `0007` (Ranking, gesetzte Plätze, Obergrenzen), `0010`: überholt durch ADR 0011 bzw. 0014; der Kopf der Datei nennt jeweils den Nachfolger.
- `learning/lessons/*.md`: Die Links der Lernkarten zeigen seit #66 auf die Ordnerstruktur aus #20 (z. B. `select/curation.py`, `extract/bsi.py`, `data/input/scope.json`). Karte #17 nennt `retries=3`; heute 6. Karte #6 nennt als Relevanzregel „erster Ressourcentyp“; seit ADR 0013 gilt die neue Regel.
- `docs/SPEC.md` (Zeile zur Relevanz) und `README.md` (Ranking, gesetzte Plätze): noch vor ADR 0011 formuliert; `docs/METHODIK.md` ist seit #65 nachgezogen. Die drei früheren Erklär-Dokumente (Datenmodell, Einführung, KI-Agenten) sind seit #66 gelöscht; ihr gültiger Inhalt steht in [DESIGN](../../docs/DESIGN.md), [ARCHITECTURE](../../docs/ARCHITECTURE.md) und [METHODIK](../../docs/METHODIK.md).

## Wenn das Lehrbuch später erweitert wird

Nach Schritt 11 (#8) kommen ein Kapitel „Preset-Gate und Workflow“ und eine Aktualisierung von Kapitel 08 (OIDC, Secrets) dazu. Nach Schritt 15 (#7) ein Kapitel „Golden Archetypes und cdk-nag“ (Allowlist, Funktionstrennung, `cdk_runner.py`).
