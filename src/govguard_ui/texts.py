"""German UI texts shared by several pages (#11)."""

DATA_WARNING = ("Keine echten oder personenbezogenen Daten eingeben. "
                "Eingaben gehen zur Inferenz an Groq in die USA.")  # ADR 0004, 0016, 0023

HELP = {
    "FAIL": "Verstoß belegt: Die Belegzeilen legen etwas fest, das der Prüfregel widerspricht. "
            "Fehlt nur eine Angabe, ist das kein FAIL, sondern eine Lücke.",
    "WARN": "Prüfbedarf mit Beleg: Die Zeilen reichen für kein klares Urteil, oder der Code hat "
            "ein PASS oder FAIL herabgestuft, das die KI nicht belegt oder der FAIL-Prüfer nicht "
            "bestätigt hat. Fachlich nachprüfen.",
    "GAP": "WARN ohne Belegzeilen: Die Eingabe beschreibt die Anforderung nicht. Eine "
           "Spezifikation ist eine offene Welt, deshalb ist das kein Verstoß, sondern eine "
           "offene Frage. Die Checkliste steht unter der Befundliste.",
    "PASS": "Einhaltung belegt: Die Belegzeilen zeigen, dass die Anforderung erfüllt ist.",
    "N/A": "Nicht anwendbar, z. B. weil der Ressourcentyp in der Architektur nicht vorkommt. "
           "In der Liste standardmäßig ausgeblendet.",
    "judge": "Ein zweiter Modellaufruf sieht je FAIL nur das Verstoßkriterium und die "
             "Belegzeilen. Bestätigt er nicht, stuft der Code auf WARN herab. „Nicht "
             "verfügbar“: Das FAIL bleibt ungeprüft stehen. Nur bei Spezifikationen.",
    "expected": "Jedes Preset hat ein festgelegtes Soll: Gesamtstatus und Pflichtbefunde. Weicht "
                "ein Report ab, zeigt GovGuard das offen, statt neu zu würfeln. Ein Klick auf "
                "einen Pflichtbefund springt zu ihm.",
    "overall": "Der strengste Status aller Befunde: FAIL vor WARN vor PASS vor N/A.",
}

TYPE_LABELS = {"spec": "Spezifikation (DSGVO, SDM)",
               "architecture": "Architektur (BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP)"}
