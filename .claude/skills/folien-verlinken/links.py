"""Plan and verify internal slide links in the Deep-Dive deck (Google Slides).

Every slide carries a code like "K6.06 · KAPITEL 6 · SPEC-AUDIT" in its chapter line;
a chapter cover ends in ".00", the map is K0.01. Targets are found by code, never by
page number.

  python links.py plan <read.json> <outdir>    -> outdir/b1.json … (updateTextStyle batches)
  python links.py verify <before.json> <after.json>

<read.json> is a saved read_presentation result with the field mask from SKILL.md.
"""

import json
import re
import sys
from pathlib import Path

CODE = re.compile(r"^(K\d+\.\d+) · ")
LIST_CODE = re.compile(r"\bK\d+\.\d+\b")
MAP_CARD = re.compile(r"^K(\d+) · ab Folie \d+")
CHAPTER_WORD = re.compile(r"KAPITEL \d+", re.IGNORECASE)
CHAPTER_REST = re.compile(r"KAPITEL (\d+)[^\n]*", re.IGNORECASE)
MAP = "K0.01"
BATCH_SIZE = 80
FIELDS = "link,foregroundColor,underline"


def load(path):
    return json.loads(Path(path).read_text())["content"]


def shapes(slide):
    for element in slide.get("pageElements", []):
        if "shape" in element:
            yield element
        for child in element.get("elementGroup", {}).get("children", []):
            if "shape" in child:
                yield child


def runs(shape):
    elements = shape["shape"].get("text", {}).get("textElements", [])
    return [t for t in elements if "textRun" in t]


def text(shape):
    return "".join(t["textRun"]["content"] for t in runs(shape))


def u16(s):
    return len(s.encode("utf-16-le")) // 2


def index_codes(deck):
    """Map code -> slide id and slide id -> (chapter-line shape, code)."""
    by_code, chapter_line = {}, {}
    for slide in deck["slides"]:
        for shape in shapes(slide):
            if m := CODE.match(text(shape)):
                by_code[m.group(1)] = slide["objectId"]
                chapter_line[slide["objectId"]] = (shape, m.group(1))
    return by_code, chapter_line


def target(shape, start, piece, dest, label):
    full = text(shape)
    begin = u16(full[:start])
    return {"shape": shape, "start": begin, "end": begin + u16(piece), "dest": dest, "label": label}


def cover_targets(slide, line, code, by_code):
    """Rule 4 (cover -> map) and rule 2 (listed codes -> their slide)."""
    found, missing = [], []
    if m := CHAPTER_WORD.search(text(line)):
        found.append(target(line, m.start(), m.group(0), by_code[MAP], f"R4 {code}"))
    else:
        missing.append(f"R4 {code}: kein „Kapitel N“ in „{text(line).strip()}“")
    listed = [(s, m) for s in shapes(slide) if s is not line for m in LIST_CODE.finditer(text(s))]
    for shape, m in listed:
        dest = by_code.get(m.group(0))
        if dest:
            found.append(target(shape, m.start(), m.group(0), dest, f"R2 {code} {m.group(0)}"))
        else:
            missing.append(f"R2 {code}: Zielcode {m.group(0)} fehlt im Deck")
    if not listed:
        missing.append(f"R2 {code}: keine Liste „Folien in diesem Kapitel“")
    return found, missing


def slide_targets(slide, line, code, by_code):
    """Rule 3: "KAPITEL N …" in the chapter line -> cover KN.00."""
    if code.endswith(".00"):
        return cover_targets(slide, line, code, by_code)
    m = CHAPTER_REST.search(text(line))
    cover = by_code.get(f"K{m.group(1)}.00") if m else None
    if not cover:
        return [], [f"R3 {code}: kein „Kapitel N“ in „{text(line).strip()}“"]
    return [target(line, m.start(), m.group(0), cover, f"R3 {code}")], []


def map_targets(deck, by_code):
    """Rule 1: each map card "K6 · ab Folie 59" -> cover K6.00."""
    slide = next(s for s in deck["slides"] if s["objectId"] == by_code[MAP])
    found = []
    for shape in shapes(slide):
        if m := MAP_CARD.match(text(shape)):
            found.append(
                target(shape, 0, m.group(0), by_code[f"K{m.group(1)}.00"], f"R1 K{m.group(1)}")
            )
    return found


def requests(t):
    """One updateTextStyle per run, keeping the run's colour and underline.

    Setting a link alone makes the API paint the text in the theme's hyperlink colour
    and underline it; sending both fields in the same request keeps the design.
    """
    out = []
    for run in runs(t["shape"]):
        start, end = run.get("startIndex", 0), run["endIndex"]
        if start >= t["end"] or end <= t["start"]:
            continue
        style = run["textRun"].get("style", {})
        out.append(
            {
                "updateTextStyle": {
                    "objectId": t["shape"]["objectId"],
                    "textRange": {
                        "type": "FIXED_RANGE",
                        "startIndex": max(start, t["start"]),
                        "endIndex": min(end, t["end"]),
                    },
                    "style": {
                        "link": {"pageObjectId": t["dest"]},
                        "foregroundColor": style.get("foregroundColor"),
                        "underline": style.get("underline", False),
                    },
                    "fields": FIELDS,
                }
            }
        )
    return out


def plan(read_path, outdir):
    deck = load(read_path)
    by_code, chapter_line = index_codes(deck)
    found, missing = map_targets(deck, by_code), []
    for slide in deck["slides"]:
        line, code = chapter_line[slide["objectId"]]
        f, m = slide_targets(slide, line, code, by_code)
        found += f
        missing += m
    reqs = [r for t in found for r in requests(t)]
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(reqs), BATCH_SIZE):
        batch = reqs[i : i + BATCH_SIZE]
        (out / f"b{i // BATCH_SIZE + 1}.json").write_text(json.dumps(batch, ensure_ascii=False))
    counts = {r: sum(t["label"].startswith(r) for t in found) for r in ("R1", "R2", "R3", "R4")}
    print(
        f"revision {deck['revisionId']} · {len(deck['slides'])} Folien · "
        f"{len(reqs)} Anfragen in {-(-len(reqs) // BATCH_SIZE)} Paketen · {counts}"
    )
    print("Nicht setzbar:", *missing or ["keine"], sep="\n  ")


def char_styles(shape):
    """Colour/underline per character, skipping line ends (they take the colour before)."""
    out = []
    for run in runs(shape):
        style = run["textRun"].get("style", {})
        key = (json.dumps(style.get("foregroundColor"), sort_keys=True), style.get("underline"))
        out += [None if ch == "\n" else key for ch in run["textRun"]["content"]]
    return out


def expected_target(source, piece, by_slide):
    """Code the link in `piece` on slide `source` must point to, or None if unexpected."""
    if m := MAP_CARD.fullmatch(piece):
        return f"K{m.group(1)}.00"
    if LIST_CODE.fullmatch(piece) and by_slide[source].endswith(".00"):
        return piece
    if by_slide[source].endswith(".00") and CHAPTER_WORD.fullmatch(piece):
        return MAP
    if m := CHAPTER_REST.fullmatch(piece):
        return f"K{m.group(1)}.00"
    return None


def verify(before_path, after_path):
    before, after = load(before_path), load(after_path)
    by_code, _ = index_codes(after)
    by_slide = {sid: code for code, sid in by_code.items()}
    old = {(s["objectId"], e["objectId"]): e for s in before["slides"] for e in shapes(s)}
    new = {(s["objectId"], e["objectId"]): e for s in after["slides"] for e in shapes(s)}
    order = [s["objectId"] for s in before["slides"]] == [s["objectId"] for s in after["slides"]]
    text_diff = [k for k in old if k not in new or text(old[k]) != text(new[k])]
    style_diff = [k for k in old if k in new and char_styles(old[k]) != char_styles(new[k])]
    links, wrong = 0, []
    for (sid, _), shape in new.items():
        for run in runs(shape):
            dest = run["textRun"].get("style", {}).get("link", {}).get("pageObjectId")
            if not dest:
                continue
            links += 1
            piece = run["textRun"]["content"]
            if expected_target(sid, piece, by_slide) != by_slide.get(dest):
                wrong.append(f"{by_slide[sid]} „{piece}“ -> {by_slide.get(dest)}")
    print(
        f"Reihenfolge gleich: {order} · Textänderungen: {len(text_diff)} · "
        f"Farbänderungen: {len(style_diff)} · interne Links: {links}"
    )
    print("Falsche Ziele:", *wrong or ["keine"], sep="\n  ")


if __name__ == "__main__":
    {"plan": plan, "verify": verify}[sys.argv[1]](*sys.argv[2:])
