"""Contracts of the measure (Maßnahme) proposal for one site (#82).

Draft pattern: the model fills only MeasureDraft; the code finds the lines and adds the anchors.
"""

from pydantic import BaseModel


class MeasureDraft(BaseModel):  # written by the LLM, one item of submit_measures; no defaults
    sentence: str  # what to change, one sentence
    from_line: int  # first and last line of the site that change (numbers of the marked document);
    to_line: int  # the code cuts the "before" from them, the model never copies it
    after: str  # the new lines that replace them; `[…]` marks a fact the model lacks
    rule_ids: list[str]  # the WARN/FAIL findings of the site this measure solves


class MeasuresResponse(BaseModel):  # schema of tool submit_measures
    measures: list[MeasureDraft]


class Measure(BaseModel):  # completed by the code: the verbatim lines and the anchors
    sentence: str
    before: str  # cut from the document by the code: verbatim by construction; empty = insert (#85)
    after: str
    line_start: int | None  # of `before`; None while `before` is empty (#85)
    line_end: int | None
    rule_ids: list[str]
    anchors: list[str]  # primary anchors of the findings, each once, in the order of rule_ids
