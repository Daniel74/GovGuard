"""The LLM groups the sections of one legal article (#53). Gets the model injected (ADR 0005).

The model names marks and the kind of each group, never a quote: the code quotes (parts.py).
"""

import json

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput
from pydantic_ai.models import Model

from govguard.models import SourceName
from kb_build.decompose.models import Decomposition
from kb_build.decompose.parts import decomposition_problems
from kb_build.extract.models import Requirement
from kb_build.llm_step import LlmCache, LlmStep, cache_key, prompt_version

INSTRUCTIONS = """\
Du zerlegst genau einen Artikel eines EU-Gesetzes in einzelne prüfbare Pflichten.
Der Artikel ist in Abschnitte geteilt. Jeder Abschnitt beginnt mit seiner Marke in eckigen
Klammern, z. B. [Art. 6 Abs. 1 lit. a]. Eine Einleitung gilt für jeden Punkt ihrer Aufzählung.
Ordne jede Marke genau einer Gruppe zu ("groups"). Je Gruppe:
- "marks": die Marken ihrer Abschnitte, genau wie in den Klammern, aber ohne Klammern.
- "kind":
  "alle_gelten": Jeder Abschnitt ist eine eigene Pflicht oder Bedingung, alle gelten zugleich
  (z. B. die Grundsätze einer Aufzählung).
  "eine_genuegt": Die Abschnitte sind Alternativen, eine davon reicht (z. B. Rechtsgrundlagen,
  Ausnahmen von einem Verbot, "eine der folgenden Bedingungen"). Nur Abschnitte eines Absatzes.
  "je_nach_risiko": Maßnahmen, die gelten, soweit das Risiko sie erfordert
  (z. B. "gegebenenfalls", "dem Risiko angemessen"). Eine Aufzählung von Maßnahmen mit
  "gegebenenfalls" oder "unter anderem" ist "je_nach_risiko", keine Alternative.
  "keine_pflicht": nur Befugnisse oder Aufgaben anderer Stellen (Mitgliedstaaten, Kommission,
  Aufsicht, Ausschuss), Hinweise wie "bleibt unberührt" und Ausnahmen von einer Pflicht.
  Rechte der betroffenen Person und Regeln zur Einstufung (z. B. wann ein System als
  hochriskant gilt) sind keine "keine_pflicht": Ordne sie "alle_gelten" zu.
  Ein Verbot, dessen Ausnahmen der Artikel in einem eigenen Absatz aufzählt (z. B. erst "ist
  untersagt", danach "gilt nicht, wenn eine der folgenden Bedingungen"), ist "keine_pflicht":
  Die Gruppe der Ausnahmen ("eine_genuegt") trägt die Prüfung. Jedes andere Verbot bleibt
  "alle_gelten", auch wenn es Ausnahmen in seinem eigenen Satz nennt.
- "rationale": ein deutscher Satz, warum diese Art.
Zitiere nicht; den Wortlaut übernimmt der Code."""

USER_PROMPT = "Quelle: {source}\nArtikel: {id} – {title}\n<artikel>\n{sections}\n</artikel>"
TOOL_NAME = "decompose_article"
TOOL_DESCRIPTION = "Gib die Gruppen der Abschnitte des Artikels an."
RETRIES = 4  # build only; the prototype needed up to 3 (#53)

split_agent = Agent(
    output_type=ToolOutput(Decomposition, name=TOOL_NAME, description=TOOL_DESCRIPTION),
    deps_type=Requirement,
    instructions=INSTRUCTIONS,
    retries=RETRIES,
    model_settings={"temperature": 0},
)


@split_agent.output_validator
def _validate(ctx: RunContext[Requirement], answer: Decomposition) -> Decomposition:
    problems = decomposition_problems(ctx.deps, answer)
    if problems:
        raise ModelRetry(" ".join(problems))
    return answer


def user_prompt(source: SourceName, article: Requirement) -> str:
    """Each lead-in once, before the first item it introduces."""
    lines, seen = [], set()
    for section in article.sections:
        if section.lead_in and section.lead_in not in seen:
            seen.add(section.lead_in)
            lines.append(f"Einleitung: {section.lead_in}")
        lines.append(f"[{section.mark}] {section.text}")
    return USER_PROMPT.format(source=source, id=article.id, title=article.title,
                              sections="\n".join(lines))


def request_version() -> str:
    """Everything the model sees besides the article itself."""
    schema = json.dumps(Decomposition.model_json_schema(), sort_keys=True)
    return prompt_version(INSTRUCTIONS, USER_PROMPT, TOOL_NAME, TOOL_DESCRIPTION, schema)


class DecompositionCache(LlmCache[Decomposition]):
    answer_type = Decomposition


class Splitter:
    """Asks the LLM once per article; a known answer comes from the cache.

    An answer that stays invalid gives `None`: the article stays whole (outcome `llm_error`),
    the run goes on, and nothing is cached.
    """

    def __init__(self, model: Model, cache: DecompositionCache | None = None) -> None:
        self.model_id, self._model = model.model_name, model
        self._step = LlmStep(cache if cache is not None else DecompositionCache())
        self._version = request_version()
        self.usage = self._step.usage
        self.counts = self._step.counts

    def __call__(self, source: SourceName, article: Requirement) -> Decomposition | None:
        prompt = user_prompt(source, article)
        key = cache_key(prompt, self._version, self.model_id)
        return self._step.cached_or_ask(key, lambda: self._ask(source, article, prompt))

    def _ask(self, source: SourceName, article: Requirement, prompt: str) -> Decomposition | None:
        return self._step.ask(
            f"decompose {source} {article.id}",
            lambda usage: split_agent.run_sync(
                prompt, model=self._model, deps=article, usage=usage).output,
            "%s %s: stays whole, invalid answer: %s", source, article.id)
