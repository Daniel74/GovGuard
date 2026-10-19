"""Build contract of the decomposition (#53): groups of sections and the decomposition protocol."""

from typing import Literal

from pydantic import BaseModel, Field

from govguard.models import SourceName

# alle_gelten: each section is a duty of its own; eine_genuegt: alternatives, one is enough;
# je_nach_risiko: each section applies as far as the risk requires; keine_pflicht: no duty
Kind = Literal["alle_gelten", "eine_genuegt", "je_nach_risiko", "keine_pflicht"]


class Group(BaseModel):  # written by the LLM
    marks: list[str] = Field(min_length=1)
    kind: Kind
    rationale: str


class Decomposition(BaseModel):  # schema of tool decompose_article
    groups: list[Group] = Field(min_length=1)


class DecomposedGroup(Group):
    anchors: list[str]  # set by the code: one per section, or one for an eine_genuegt group


class ArticleDecomposition(BaseModel):  # file decompositions_spec.json, the decomposition protocol
    source: SourceName
    requirement_id: str  # the article, e.g. "Art. 32"
    outcome: Literal["decomposed", "llm_error"]  # llm_error: the article stays whole
    groups: list[DecomposedGroup]
