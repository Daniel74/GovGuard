# 0020 – FAIL nur bei festgelegtem Verstoß

_Ergänzt [ADR 0017](0017-beleg-per-zeilenverweis.md). Umsetzung und Messungen: #28, Umbau des Katalogs: #29._

## Kontext

- Seit #26 wird ein FAIL ohne Beleg WARN. Trotzdem verfehlt `spec-wohngeld-openapi` sein `expected` (WARN): Beide Modelle vergeben FAILs *mit* Beleg, die keinen Verstoß zeigen, z. B. Bedrock zu Art. 12 mit dem Abschnitt „Rechte der betroffenen Personen“. Ob ein Beleg einen Verstoß zeigt, ist eine Bedeutungsfrage, die kein Code-Gate entscheidet.
- Bei der Architektur gilt das Gegenteil: Ein Template ist ein Bauplan. Fehlt eine Einstellung, gilt der Standardwert, und das ist oft der Verstoß.
- 130 von 151 `violation_if` im Spec-Katalog beschreiben ein Fehlen, z. B. „Die Spezifikation enthält kein Verfahren …“. Auch mit der Regel der offenen Welt vergibt Groq noch 50 FAILs, fast alle mit „keine/fehlt“ (Messung Anlauf 1b, #28).

## Entscheidung

- Eine Spezifikation ist eine **offene Welt**: Was sie nicht erwähnt, kann anderswo geregelt sein. Ein Template ist eine **geschlossene Welt**: Was fehlt, ist der Standardwert. Welche Welt gilt, entscheidet der Code über die Audit-Art, nicht das Modell.
- Nur im Spec-Audit gilt die Prompt-Regel (`SPEC_FAIL_RULE`): Beschreibt `violation_if` ein Fehlen, belegt fehlender Text nur „nicht beschrieben“, also WARN. FAIL gibt es nur, wenn die Belegzeilen etwas festlegen, das der Prüfregel widerspricht. `rationale` nennt diese Festlegung.
- Die gemeinsame WARN-Zeile heißt nur noch „Aus der Eingabe nicht entscheidbar“, weil „was fehlt, ist WARN“ für Templates falsch ist. Audit und Inventar-Vorlauf laufen mit `temperature: 0` und höchstens 8.000 Output-Tokens je Aufruf.
- Kein Gate und kein neues Feld: Ein Feld für das erfüllte Kriterium hilft nicht, solange das Kriterium selbst ein Fehlen beschreibt. Deshalb formuliert #29 `violation_if` im Spec-Katalog als Festlegung um.

## Konsequenzen

- Die Regel steht nur im Prompt, auch die Pflicht für `rationale`. Ein falsches FAIL mit Beleg bleibt möglich und fällt nur in der Messung gegen `expected` auf. Allein reicht die Regel nicht, erst mit #29 kann `expected` grün werden.
- Gemessen werden in #29 auch die Gegenproben (Art. 9 bleibt FAIL) und die Schwankung: die Zahl der Prüfregeln, deren Status sich zwischen zwei Läufen ändert. `temperature: 0` macht Läufe nicht identisch.
- Ein Bedrock-Retry lief in einer Schleife bis 64.000 Output-Tokens (204 s). Mit der Obergrenze bricht eine Schleife nach ca. 25 s ab, normal sind unter 4.000 Tokens. Der abgeschnittene Tool-Call beendet das Audit sofort fail closed, ohne Retry, aber innerhalb der 180 s (ADR 0018).
- ~~Offen: Eine Architektur als Freitext ist eigentlich auch offene Welt, wird aber heute wie ein Template geprüft.~~ Gelöst mit #46, siehe Nachtrag.

## Nachtrag (#29)

- Der Formulier-Prompt fürs Spec-Audit verlangt als `violation_if` eine Festlegung, auch einen erklärten Verzicht oder Aufschub. Im Build prüft ein **LLM-Prüfer** (`judge_violation`) jedes Spec-`violation_if`. Beschreibt es ein Fehlen, geht seine Begründung als Retry an den Formulierer. Scheitert der Prüfer, bricht der Build ab (fail closed).
- Verworfen: eine Sperrliste („kein“, „fehlt“, „vage“). Sie schließt aus Wörtern auf die Bedeutung. „legt nicht fest“ und „legt fest, dass … nicht“ unterscheiden sich nur in der Wortstellung, und jede neue Umschreibung bräuchte einen neuen Eintrag.
- Konsequenz: Ein LLM prüft ein LLM, das Urteil ist nicht reproduzierbar. Deshalb läuft der Prüfer nur im Build, die Zeile `spec quality judge` zählt seine Treffer, und den Beweis liefert weiter die Messung gegen `expected`. Er kostet einen Request je gültigen Entwurf, im ersten Lauf 245 von 619 Requests des Spec-Builds.
- Jeder Retry und jeder Abbruch zählt genau einmal, und zwar bei dem Schritt, der ihn ausgelöst hat: Treffer und Ausfälle des Prüfers zählen nur bei `judge`, Schema- und Code-Fehler nur bei `formulate`. Lehnt der Prüfer bis zum Limit ab, ist das ein `llm_error` bei `formulate`, denn der Formulierer hat keine gültige Regel geliefert.

## Nachtrag (#31): FAIL-Prüfer zur Laufzeit

- **Kontext:** Groq vergibt mit dem neuen Katalog weiter FAILs mit Fehlen-Begründung (8–12 bei `spec-wohngeld-openapi`). Diagnose: Allein laufen dieselben Regeln stabil auf WARN, in ihren Original-Paketen einmal mit 6 FAILs, einmal ohne. Ursache sind Nachbarregeln und Zufall, nicht Regel oder Katalog.
- **Entscheidung:** Im Spec-Audit prüft der **FAIL-Prüfer** (`judge_fails`) alle FAILs in einem Request mit demselben Modell, für Bedrock und Groq (ADR 0016: gleiche Gates). Er sieht je FAIL nur Verstoßkriterium und Belegzeilen. Die Begründung des Auditors fehlt bewusst: Mit ihr wiederholte Groq sie und bestätigte 12 von 13 falschen FAILs, ohne sie 0. Bestätigt er nicht, stuft der Code ohne Retry auf WARN herab. Fehlen Urteile oder bricht das Schema, gibt es genau einen Retry; er zählt in `retries` wie bei einem Prüfpaket. Fällt der Prüfer aus oder fehlt danach noch ein Urteil, bleibt das FAIL ungeprüft stehen: strengerer Status, kein fail closed. Jedes Urteil steht in `corrections`, der Report zählt sie (`fail_judge`).
- **Abweichung vom Nachtrag #29** („Prüfer nur im Build“): Das Urteil bleibt nicht reproduzierbar. Darum stuft es nur herab, nie hinauf, und steht sichtbar im Report.
- **Verworfen:**
  - Ein weiterer Satz in `SPEC_FAIL_RULE`: Die Regel verlangt die Festlegung schon, Groq ignoriert sie.
  - Ein Code-Gate auf `rationale`: Das wäre eine Sperrliste, siehe oben.
  - Pakete auflösen: ca. 9-fache Tokens, mit dem Groq-Limit ca. 18 min statt 180 s, und der Zufall bliebe.
- **Konsequenzen:** Ein Request mehr je Spec-Audit mit FAIL, mit wenigen tausend Tokens. Ein fälschlich bestätigtes FAIL bleibt möglich und fällt nur in der Messung gegen `expected` auf.

## Nachtrag (#46): Architektur als Freitext ist offene Welt

- **Kontext:** `arch-protokollarchiv` (Freitext, Groq) bekam 4–9 FAILs je Lauf wie „keine LifecycleConfiguration erwähnt“, Gesamtstatus FAIL statt WARN.
- **Entscheidung:** Die Welt hängt nicht mehr an der Audit-Art, sondern an der Eingabe. Geschlossen ist nur, was der Code als Bauplan liest: CloudFormation-JSON (`template_resource_types`, wie beim Inventar). Für alles andere gelten Prompt-Regel (`OPEN_WORLD_FAIL_RULE`) und FAIL-Prüfer. Beide haben Platzhalter für Gegenstand und Beispielpaar (`OpenWorld`); für das Spec-Audit entsteht zeichengenau der alte Text. Der Report speichert die Welt (`closed_world`), damit die UI den FAIL-Prüfer nur beim Template als „entfällt“ zeigt. Einschränkung: CloudFormation-YAML und Terraform gelten als offene Welt, solange der Code sie nicht liest; YAML folgt in #48.
- **Messung** (Groq, 2 Läufe): FAILs wegen Fehlens nach dem Prüfer 0 und 0 (der Prüfer stufte 1 bzw. 2 herab). Es blieb 1 FAIL mit Festlegung (KONF.11.7.2.1, „REST, regional“, zu wörtlich, #47). CIS 3.1.4 PASS in beiden Läufen, DET.3.1 WARN und PASS („1 Jahr“ nicht als `RetentionInDays` gelesen); beides ist eine zu wörtliche Prüfregel und nach #47 verschoben. Die Schwankung beträgt 9 Prüfregeln.

## Nachtrag (#47): Zu wörtliche Architektur-Regeln

- **Kontext:** Ca. 25 von 166 Architektur-Regeln waren enger als ihre Quelle, gehäuft bei BSI (ca. 17 von 34): eine erfundene Umsetzung als Pflicht (feste CIDR, Ports, ARN, Tags) oder Vorhandensein statt Einschränkung (z. B. `Ingress: []`). Ursache: `ARCHITECTURE_CRITERIA` verlangte „die konkrete Eigenschaft mit Wert“.
- **Entscheidung:** Kriterien nennen zuerst den Sachverhalt in Worten, dann Typ und Eigenschaft; mehrere Umsetzungen werden aufgezählt, Werte nur aus der Quelle, „einschränken“ nennt nur das Offene; „gleichwertig“ gilt als vages Wort. Voll-Rebuild des Architektur-Katalogs (175 Regeln, Auswahl seit #24), kein Teil-Rebuild: ein Katalog, eine Prompt-Version.
- **Messung** (Groq): Stichprobe ca. 25 → ca. 9 zu enge Regeln. Der Satz zu „einschränken“ wirkt (2 von 4 voll, 1 halb; Kontrollgruppe ohne eigenen Satz 1 von 4), der Satz zu Allow/Deny nicht (0 von 4); er bleibt, weil der Katalog mit ihm gebaut ist. `arch-fristenwecker` und `arch-antragseingang-fehlerhaft` erreichen `expected`; `arch-protokollarchiv` WARN in 2 Läufen, S3.5 und CIS 3.1.4 PASS, Schwankung 4 statt 9. DET.3.1 bleibt WARN: „1 Jahr“ wird gelesen, aber die Regel nennt den Platzhalter `<Mindestfrist>` (#50).
- **Abweichung:** `arch-protokollarchiv` verfehlt `expected` (DET.3.1). Gegen die Abbruchregel aus dem Grilling bleibt der neue Katalog, weil das Muster behoben ist. Bekannte Rückschritte (#50): S3.5 nennt Deny bei `false` ausdrücklich als Verstoß, das PASS im Lauf ist Zufall; Platzhalter in 12 statt 3 Regeln.
- **Verworfen: Umsetzungs-Prüfer** im Build, ein LLM fragt je Regel „Wertet `violation_if` eine übliche Umsetzung als Verstoß?“. Er widersprach fast jeder zweiten Regel, fand bei jeder Nachfrage eine neue Alternative (DLS.2.2: sechsmal, u. a. CloudFront) und schwächte Sicherheitsregeln ab („SOLLTE, daher ist ein unverschlüsselter Bucket zulässig“). Ein zu weiches PASS fällt niemandem auf, ein zu enges FAIL schon.
- **Konsequenz:** Ein Rebuild bricht mit Groq oft an einer einzelnen Regel ab (5 von 7 Läufen am 18.10.), u. a. weil das Eigenschafts-Gate Werte wie `ELBSecurityPolicy-…` als Eigenschaft liest (#49).

## Fachgespräch-Satz

„Eine Spezifikation oder eine Architektur als Freitext ist eine offene Welt: Was sie nicht erwähnt, ist Prüfbedarf, also WARN. Ein Template, das der Code liest, ist eine geschlossene Welt, dort bedeutet eine fehlende Einstellung den unsicheren Standardwert, also FAIL.“
