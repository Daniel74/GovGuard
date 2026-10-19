"""PROTOTYPE - wegwerfen. Frage: Zerlegt Groq gpt-oss-120b Gesetzesartikel zuverlässig in
Einzelpflichten und unterscheidet "alle gelten" von "eine genügt"? Kein Code für src/.

Aufruf: uv run python <dieses Skript> [Läufe je Artikel]
"""

import io
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput

from govguard.groq_services import groq_model
from govguard.text import contains_quote, normalize
from kb_build.extract import formex

SOURCES = Path("data/intermediate/sources")
CASES = [("DSGVO", "5"), ("DSGVO", "6"), ("DSGVO", "9"), ("DSGVO", "32"), ("KI-VO", "6")]


def _xml(source: str) -> bytes:
    if source == "DSGVO":
        return (SOURCES / "dsgvo_02016R0679-20160504.xml").read_bytes()
    zf = zipfile.ZipFile(io.BytesIO((SOURCES / "ki_vo_02024R1689-20260727.zip").read_bytes()))
    return zf.read(next(n for n in zf.namelist() if not n.endswith(".doc.xml")))


def _text_without_lists(el: ET.Element) -> str:
    copy = ET.fromstring(ET.tostring(el))
    for parent in copy.iter():
        for child in list(parent):
            if child.tag == "LIST":
                parent.remove(child)
    return normalize(formex._render(copy))


def segments(source: str, number: str) -> dict[str, str]:
    """Label -> text: "Abs. 1" (intro without list) and "Abs. 1 lit. a" (one list item)."""
    root = ET.fromstring(_xml(source))
    article = next(a for a in root.iter("ARTICLE")
                   if a.attrib["IDENTIFIER"].lstrip("0").lower() == number)
    parags = list(article.iter("PARAG")) or [article]
    out = {}
    for parag in parags:
        no = parag.find("NO.PARAG")
        label = f"Abs. {no.text.strip('() ')}" if no is not None else "Text"
        body = ET.fromstring(ET.tostring(parag))
        for child in list(body):
            if child.tag in {"NO.PARAG", "TI.ART", "STI.ART"}:
                body.remove(child)
        out[label] = _text_without_lists(body)
        for lst in body.iter("LIST"):
            for item in lst.findall("ITEM"):
                np_no = item.find("NP/NO.P")
                letter = np_no.text.strip("() ") if np_no is not None else "?"
                out[f"{label} lit. {letter}"] = normalize(formex._render(item)).removeprefix(
                    f"{np_no.text} " if np_no is not None else "")
    return out


class Duty(BaseModel):
    anchor: str  # one of the segment labels, e.g. "Abs. 1 lit. a"
    quote: str  # verbatim from that segment
    duty: str  # one German sentence: what must be done or must hold


class Group(BaseModel):
    topic: str
    kind: Literal["alle_gelten", "eine_genuegt"]
    duties: list[Duty]


class Decomposition(BaseModel):
    groups: list[Group]


INSTRUCTIONS = """\
Du zerlegst genau einen Artikel eines EU-Gesetzes in einzelne prüfbare Pflichten oder Bedingungen.
Der Text ist in Abschnitte mit Marken wie [Abs. 1] oder [Abs. 1 lit. a] geteilt.
- Jede Pflicht nennt die Marke ("anchor") genau eines Abschnitts und ein wörtliches Zitat daraus
  ("quote", mindestens 15 Zeichen) sowie einen deutschen Satz ("duty").
- Fasse Pflichten in Gruppen ("groups") zusammen. "kind" ist "alle_gelten", wenn jede Pflicht der
  Gruppe zugleich gilt, und "eine_genuegt", wenn der Text Alternativen nennt und eine davon reicht
  (z. B. Rechtsgrundlagen, Ausnahmen von einem Verbot, "eine der folgenden Bedingungen").
- Enthält ein Abschnitt mehrere Pflichten, zerlege ihn. Lasse Befugnisse von Mitgliedstaaten,
  Kommission oder Aufsicht weg."""


RETRIES: list[str] = []


def build_agent(segs: dict[str, str]) -> Agent:
    agent = Agent(groq_model(), instructions=INSTRUCTIONS, retries=4,
                  output_type=ToolOutput(Decomposition, name="submit_decomposition"))

    @agent.output_validator
    def _check(ctx: RunContext, out: Decomposition) -> Decomposition:
        problems = []
        for g in out.groups:
            for d in g.duties:
                d.anchor = d.anchor.strip("[] ")  # the model copies the brackets of the marks
                if d.anchor not in segs:
                    problems.append(f"Marke {d.anchor!r} gibt es nicht.")
                elif not contains_quote(segs[d.anchor], d.quote):
                    problems.append(f"Zitat steht nicht wörtlich in [{d.anchor}]: {d.quote[:60]!r}")
        if problems:
            RETRIES.append(problems[0])
            raise ModelRetry(" ".join(problems[:5]))
        return out

    return agent


def show(source: str, number: str, out: Decomposition, requests: int) -> None:
    print(f"\n=== {source} Art. {number}  ({requests} Anfragen)")
    for g in out.groups:
        anchors = ", ".join(d.anchor.replace("Abs. ", "") for d in g.duties)
        print(f"  [{g.kind:12}] {g.topic[:60]:60} <- {anchors}")


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for source, number in CASES:
        segs = segments(source, number)
        prompt = "\n".join(f"[{k}] {v}" for k, v in segs.items())
        for _ in range(runs):
            try:
                result = build_agent(segs).run_sync(f"Quelle: {source} Art. {number}\n{prompt}")
                show(source, number, result.output, result.usage.requests if not callable(result.usage) else result.usage().requests)
            except Exception as error:  # noqa: BLE001 - prototype
                print(f"\n=== {source} Art. {number}: FEHLER {type(error).__name__}: {str(error)[:150]}")
            if RETRIES:
                print("     Retry-Gründe:", " | ".join(r[:110] for r in RETRIES))
                RETRIES.clear()


if __name__ == "__main__":
    main()
