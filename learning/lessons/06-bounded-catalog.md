# #6 Bounded Catalog und Auswahlprotokoll
## Was es tut
Jede Anforderung aller Quellen bekommt genau ein Urteil im Auswahlprotokoll. Alles, was prüfbar ist und einen Dienst im Prüfumfang betrifft, kommt in den Bounded Catalog, ohne Obergrenze. Das LLM beantwortet nur „prüfbar?“ und „welche Ressourcentypen?“, der Code entscheidet über die Aufnahme.
`extracted/*.json → Vorfilter (Code) → LLM-Urteil (Cache) → Relevanz (Code) → verdicts_*.json + selection_*.json → Gates`
## Wo im Code
- [curation.py](../../src/kb_build/curation.py): ein Urteil je Anforderung, Gate Pflichtanker, Gate Abdeckung
- [classify.py](../../src/kb_build/classify.py): Prompt mit Prüfumfang, Judge mit Cache
- [scope.json](../../data/scope.json): der Prüfumfang, Dienst → CloudFormation-Typen
## Entscheidung und Warum
- **Vollständig statt Top-K:** Relevant ist, wessen erster Ressourcentyp im Prüfumfang liegt. Eine Obergrenze ließ Art. 32 und alle Serverless-Dienste herausfallen; so bekommt jede Regel einen Befund (BSI: Nachvollziehbarkeit).
- **Das LLM urteilt, der Code wählt aus:** Das LLM kann weder Regeln erfinden noch aussortieren, und jede Code-Entscheidung hat einen festen Begründungssatz. Das Ergebnis ist prüfbar und reproduzierbar (temperature 0, Cache).
## Prüfungsbegriffe
- **Bounded Catalog:** feste Menge aller prüfbaren und relevanten Prüfregeln, die in jedem Audit vollständig bewertet wird
- **Auswahlprotokoll:** je Anforderung Ergebnis (selected, prefiltered, not_relevant, not_testable, llm_error) mit Begründung
- **Abdeckungs-Gate:** jede Komponente der Archetypen braucht mindestens eine Prüfregel, sonst bricht der Build ab
## Merksatz
„Bei uns fällt keine Regel heraus, weder durchs Retrieval noch durch eine Obergrenze: Was nicht anwendbar ist, entscheidet der Code nachvollziehbar, und alles andere bekommt einen Befund.“
## Abruffragen
1. Welche zwei Aufgaben haben LLM und Code bei der Aufnahme in den Bounded Catalog?
2. Wann ist eine Anforderung „relevant“, und was passiert mit einer Anforderung, deren erster Typ CloudTrail ist?
3. Welche zwei Gates gibt es, und was passiert, wenn sie nicht erfüllt sind?
