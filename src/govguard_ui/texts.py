"""German UI texts shared by several pages (#11)."""

from govguard_ui.style import LOOKS, STATUS_FILTERS

DATA_RULE = "Keine personenbezogenen oder vertraulichen Daten eingeben."  # ADR 0004, 0016, 0023

OPEN_WORLD_ONLY = "Nur bei offener Welt: Spezifikation, Architektur als Freitext."  # ADR 0020
HELP = {  # help on the report head; status help lives in style.LOOKS
    "judge": f"Ein Verstoß ist ein schwerer Vorwurf. Deshalb prüft ein zweiter Modellaufruf jeden "
             f"Befund „{LOOKS['FAIL'].label}“ nach. Er sieht nur das Verstoßkriterium der "
             "Prüfregel und die Belegzeilen, nicht die erste Begründung. Die Zahl nennt die "
             "geprüften Verstöße.\n\n"
             f"- **bestätigt:** Der Befund bleibt „{LOOKS['FAIL'].label}“.\n"
             f"- **herabgestuft:** Der Code setzt ihn auf „{LOOKS['WARN'].label}“, der Befund "
             f"zeigt „↓ herabgestuft von {LOOKS['FAIL'].label}“.\n"
             "- **nicht verfügbar:** Der Aufruf ist ausgefallen, der Verstoß bleibt ungeprüft "
             "stehen.\n\n" + OPEN_WORLD_ONLY + " Bei CloudFormation-JSON entfällt er: Dort ist "
             "ein fehlender Wert der Standardwert und darf ein Verstoß sein.",
    "expected": "Jeder Musterfall hat ein festgelegtes Soll: Gesamtstatus und Pflichtbefunde. "
                "Weicht ein Report ab, zeigt GovGuard das offen, statt neu zu würfeln. Ein Klick "
                "auf einen Pflichtbefund springt zu ihm.",
    "conditions": "Manche Prüfregeln gelten nur unter einer Bedingung, z. B. die KI-VO nur für ein "
                  "KI-System. Vor dem Audit prüft die KI, was die Eingabe zu jeder Bedingung "
                  "sagt. Nur ein **nein** mit Beleg macht Prüfregeln nicht anwendbar. Der Pfeil "
                  "an jeder Bedingung zeigt Erklärung und Beleg.",
    "gaps": "Eine Lücke ist eine Prüfregel, zu der die Eingabe nichts sagt. Das ist kein Verstoß, "
            "sondern eine offene Frage: vor der Umsetzung klären oder bewusst ausschließen. Im "
            f"JSON-Report: {LOOKS['GAP'].code}. Die Lücken stehen nicht in der Befundtabelle oben. "
            "Lücken unter einer Bedingung, zu der die Eingabe schweigt, stehen getrennt unter "
            "„Nur wenn …“: Trifft die Bedingung nicht zu, entfallen sie.",
    "multi_section": "Die Belege dieser Befunde liegen in mehreren Abschnitten. Ein Balken am Rand "
                     "gehört zu genau einem Abschnitt, darum stehen diese Befunde hier "
                     "gesammelt, mit Begründung und Empfehlung.",
    "document": "Eine Fundstelle ist ein Dokumentabschnitt (Kapitel, Ressource oder Pfad), in dem "
                "mindestens ein Befund liegt. Jede Zeile gehört zu genau einer Fundstelle, darum "
                "überschneiden sich die Balken nie.",
    "without_lines": "Diese Befunde nennen keine Zeilen, z. B. ein nicht anwendbarer Befund oder "
                     "einer, dessen Zeilenbereich der Code gestrichen hat. Lücken stehen getrennt "
                     "darunter.",
    "overall": "Der strengste Status aller Befunde: "
               + " vor ".join(LOOKS[name].label for name in STATUS_FILTERS) + ".",
}

VALUE_WORDS = {"yes": "ja", "no": "nein", "unstated": "nicht genannt"}  # result of a condition

TYPE_LABELS = {"spec": "Spezifikation (DSGVO, KI-VO, SDM)",
               "architecture": "Architektur (BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP)"}
TYPE_CHOICES = {  # radio options on "Audit erstellen": norms and input formats (#41)
    "spec": "**Spezifikation** · DSGVO, KI-VO, SDM · Markdown oder OpenAPI",
    "architecture": "**Architektur** · BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP · "
                    "CloudFormation-JSON, Terraform oder Freitext",
}
