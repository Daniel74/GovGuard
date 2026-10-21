# #13 Quellen FSBP und C5 (Prowler-Parser)

## Was es tut
CIS, AWS FSBP und BSI C5 kommen alle als Prowler-JSON vom selben Tag `5.44.0`. Ein gemeinsamer Parser liest sie; jede Quelle beschreibt nur ihr Format und ihren Vorfilter. Nach dem Vorfilter bleiben CIS 54 von 70, FSBP 150 von 286, C5 300 von 610, und jede verworfene Anforderung trägt einen festen Begründungssatz.
`sources.json (Tag + SHA-256) → source_fetch → prowler.extract(FORMAT) → prefilter() → None | Begründungssatz → cis/fsbp/c5.json (nur lokal)`

## Wo im Code
- [prowler.py](../../src/kb_build/extract/prowler.py): ein Parser für alle drei; `ProwlerFormat` sagt, woher Anker, Titel, Text und Attribute kommen.
- [fsbp.py](../../src/kb_build/extract/fsbp.py): Vorfilter über `Attributes.Service`; `EC2` und `ELB` laufen ganz durch, die Relevanz in #6 sortiert Instanzen und Classic LB aus.
- [c5.py](../../src/kb_build/extract/c5.py): Vorfilter über den Bereich vor dem Bindestrich (OPS, IAM, CRY, COS, PSS).

## Entscheidung und Warum
- **Nur die Texte, nicht Prowlers Check-Zuordnung:** Prowler-Checks prüfen ein laufendes AWS-Konto über die API; GovGuard prüft eine Architektur vor dem Deploy. Außerdem ist die Zuordnung Prowlers Auslegung, kein Normtext. Primäranker und Zitat müssen aus der Anforderung selbst stammen (BSI C5, Nachweis statt Behauptung).
- **Fester Begründungssatz je Verwurf:** Der Vorfilter gibt `None` oder einen Satz aus den Konstanten zurück. So steht im Auswahlprotokoll für jede Anforderung, warum sie fehlt, auch wenn das LLM sie nie gesehen hat (DSGVO Art. 5 Abs. 2, Rechenschaftspflicht).

## Fachbegriffe
- **Abgeleitete Quelle**: Prowler gibt fremde Normtexte weiter; wir pinnen Commit und Hash und checken die Texte wegen ungeklärter Lizenz nicht ein.
- **Gemeinsamer Parser**: ein Lesecode für drei Formate; eine neue Prowler-Quelle braucht nur ein neues `ProwlerFormat`.
- **Vorfilter vs. Relevanz**: Der Vorfilter sortiert grob nach Metadaten (Dienst, Bereich, Kapitel), die Relevanz später genau nach Ressourcentyp im Prüfumfang.

## Merksatz
„Von Prowler übernehmen wir nur den Normtext, nie die Prüflogik, und jede Anforderung, die wir verwerfen, bekommt einen festen Grund ins Protokoll.“

## Abruffragen
1. Warum übernimmt GovGuard aus Prowler nur die Texte und nicht die Check-Zuordnung?
2. Warum lässt der FSBP-Vorfilter `EC2` und `ELB` ganz durch, und wer sortiert später aus?
3. Was gibt ein Vorfilter für eine verworfene Anforderung zurück, und wozu dient das?
