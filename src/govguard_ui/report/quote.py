"""The verbatim quote of evidence lines, in whole sentences; pure, no Streamlit (#61).

A sentence ends at . ! or ? before a space or the end; not after a number, a word of one or
two letters ("z. B.") or before a lower-case letter or digit ("Art. 6", "lit. f", "Inc. mit").
A blank line ends a sentence too. The quote may reach 2 lines before and after the evidence.
"""

import re

from govguard.condition_models import LineRange

QUOTE_LIMIT = 240
REACH = 2  # lines before and after the evidence the quote may take in
ELLIPSIS = "…"
_TERMINATOR = re.compile(r"[.!?](?=\s|$)")


class _Flat:
    """The document as one string; line n spans text[starts[n]:ends[n]] (0-based)."""

    def __init__(self, text: str) -> None:
        rows = [" ".join(row.strip(" |-").split()) for row in text.splitlines()]
        self.starts: list[int] = []
        self.ends: list[int] = []
        offset = 0
        for row in rows:
            self.starts.append(offset)
            self.ends.append(offset + len(row))
            offset += len(row) + 1
        self.text = " ".join(rows)
        self.cuts = self._cuts(rows)

    def _cuts(self, rows: list[str]) -> list[int]:
        cuts = {m.end() for m in _TERMINATOR.finditer(self.text) if self._ends_sentence(m.start())}
        for n, row in enumerate(rows):
            if row and (n == len(rows) - 1 or not rows[n + 1]):
                cuts.add(self.ends[n])  # a paragraph ends
            if row and (n == 0 or not rows[n - 1]):
                cuts.add(self.starts[n])  # a paragraph begins
        return sorted(cuts)

    def _ends_sentence(self, at: int) -> bool:
        if self.text[at] != ".":
            return True
        word = self.text[self.text.rfind(" ", 0, at) + 1:at]
        following = self.text[at + 1:].lstrip()[:1]
        short = word.isalpha() and len(word) <= 2
        return not (word[-1:].isdigit() or short or following.islower() or following.isdigit())

    def sentence_start(self, at: int) -> int:
        start = max((c for c in self.cuts if c <= at), default=0)
        return start + len(self.text[start:]) - len(self.text[start:].lstrip())

    def sentence_end(self, at: int) -> int:
        return min((c for c in self.cuts if c >= at), default=len(self.text))


def _begin(flat: _Flat, first: int) -> tuple[int, bool]:
    """Where the quote starts, and whether the sentence was cut by the reach."""
    a, line_end = flat.starts[first], flat.ends[first]
    if flat.sentence_start(a) == a:
        return a, False
    inside = [c for c in flat.cuts if a < c < line_end]
    if inside:  # the line opens with the tail of an earlier sentence: skip it
        return flat.sentence_start(inside[0] + 1), False
    reach = flat.starts[max(0, first - REACH)]
    start = flat.sentence_start(a)
    return max(start, reach), start < reach


def _stop(flat: _Flat, last: int) -> tuple[int, bool]:
    reach = flat.ends[min(len(flat.ends) - 1, last + REACH)]
    end = flat.sentence_end(flat.ends[last])
    return min(end, reach), end > reach


def _one(flat: _Flat, lines: LineRange) -> str:
    first = max(0, min(lines.line_start, len(flat.starts)) - 1)
    last = max(first, min(lines.line_end, len(flat.ends)) - 1)
    begin, cut_front = _begin(flat, first)
    stop, cut_back = _stop(flat, last)
    text = flat.text[begin:stop].strip()
    text = f"{ELLIPSIS} {text}" if cut_front else text
    text = f"{text} {ELLIPSIS}" if cut_back else text
    if len(text) > QUOTE_LIMIT:
        text = text[:QUOTE_LIMIT - 2].rstrip() + f" {ELLIPSIS}"
    return text


def quote(text: str, ranges: list[LineRange]) -> str:
    """One quote per range, joined by an ellipsis."""
    flat = _Flat(text)
    return f" {ELLIPSIS} ".join(_one(flat, lines) for lines in ranges)
