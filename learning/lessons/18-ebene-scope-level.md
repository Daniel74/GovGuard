# #18 Stufe ② verwirft kontoweite Pflichten (CloudTrail-Lücke)

## Was es tut
Das LLM sagt in Stufe ② zusätzlich, **wessen** Pflicht eine Anforderung ist: Workload (`template`), Konto (`account`), Personen (`people`) oder Cloud-Anbieter (`provider`). Bei Architektur nimmt der Code nur `template` auf, alles andere wird `not_relevant` mit festem Satz im Auswahlprotokoll. So fliegen CIS 4.4 (CloudTrail-Bucket) und C5 OPS-16.01B (MFA für Admins) raus, die vorher bei jedem Bucket bzw. jeder Lambda-Rolle falsche WARN/FAIL erzeugten.
`Anforderung → LLM: prüfbar? + scope_level + Ressourcentypen → Code: Ebene ≠ template → not_relevant → Gates → selection_arch.json`

## Wo im Code
- [select/models.py](../../src/kb_build/select/models.py): Feld `scope_level` in `Classification`, Default `template`.
- [classify.py](../../src/kb_build/select/classify.py): Prompt erklärt die vier Ebenen; bei Spec erzwingt der Code `template`.
- [curation.py](../../src/kb_build/select/curation.py): `_not_relevant_reason` setzt den festen Satz aus `LEVEL_SENTENCES`.

## Entscheidung und Warum
- **Das LLM urteilt, der Code wählt aus:** Das LLM liefert nur die Ebene, die Konsequenz zieht deterministischer Code. Damit ist die Auswahl nachvollziehbar und jede Code-Entscheidung hat einen festen Begründungssatz (BSI: Nachweisbarkeit, ADR 0011).
- **Nur Pflichten des Workloads ins Architektur-Audit:** Konto-Pflichten wie Root-MFA oder kontoweiter CloudTrail sind an keinem Template entscheidbar; dafür gibt es Prowler oder Security Hub. Weniger falsche Befunde heißt auch weniger LLM-Aufrufe im Audit (FinOps: 172 statt 189 Anforderungen).

## Fachbegriffe
- **Shared Responsibility Model**: AWS teilt Sicherheitspflichten auf Anbieter, Konto und Workload auf; GovGuard prüft nur die Workload-Schicht.
- **Ebene** (`scope_level`): wessen Pflicht eine Anforderung ist; nur `template` ist „relevant“ für das Architektur-Audit.
- **Abdeckungs-Gate**: Build-Abbruch, wenn eine Komponente eines Archetyps keine ausgewählte Anforderung mehr hat; deshalb nennt der Prompt jetzt alle betroffenen Ressourcentypen.

## Merksatz
„Prüfbar und relevant reicht nicht: Eine Pflicht, die dem Konto oder der Person gehört, darf kein Template durchfallen lassen. Das LLM sagt, wessen Pflicht es ist, der Code zieht die Konsequenz.“

## Abruffragen
1. Welche vier Werte kennt `scope_level`, und welcher davon kommt ins Architektur-Audit?
2. Warum setzt der Code `not_relevant` und nicht das LLM selbst, und was steht dann im Auswahlprotokoll?
3. Warum musste der Prompt im echten Lauf zusätzlich „alle CloudFormation-Typen“ verlangen, welches Gate hätte sonst gebrochen?
