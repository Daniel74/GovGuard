# LLM uncertainty (probabilistic core, deterministic shell)

**When this concern applies:** The system calls a large language model (LLM) at run time and uses its output as data, a decision, or an action. It applies whether the model is hosted by the operator or consumed as an external service.

**Why it matters:** An LLM answers probabilistically. It can invent content (hallucination), return a different answer for the same input on the next run, follow instructions hidden in its input (prompt injection), or break the expected output format. Without a deterministic shell around it, these errors reach users and downstream systems unnoticed.

**Standards / references:** BSI AIC4 (AI Cloud Service Compliance Criteria Catalogue), BSI "Generative KI-Modelle – Chancen und Risiken für Industrie und Behörden", OWASP Top 10 for LLM Applications. AIC4 predates LLM services and targets providers that train models; the mappings below apply its criteria by analogy and name the criterion each question stems from.

## Per-view prompts

### Logical view
- Is the LLM drawn as one bounded component with typed inputs and outputs, and are the deterministic components (schema validator, rule checks, evidence store) shown separately around it? (AIC4 PF-04 Model Selection and Suitability, model boundaries; BSI R4)
- Does the model only propose, and does a deterministic component decide? Flag any path where raw model output becomes a verdict, a record, or a command. (AIC4 PF-09 Impact of Automated Decisionmaking; OWASP LLM05 Improper Output Handling)
- Is there an explicit trust boundary between untrusted text (user input, retrieved documents) and the model's instructions? (AIC4 SR-06 Implementation of Countermeasures; OWASP LLM01 Prompt Injection; BSI R26, R28)
- Does every model claim point to a source the user can check (quote, document id, rule id), and is that source store a named component? (AIC4 DM-03 Traceability of the Data Source, EX-02 Testing the Explainability of the Service; OWASP LLM09 Misinformation)
- What rights does the model have (tools, write access, external calls)? Is it limited to the minimum? (AIC4 SR-06; OWASP LLM06 Excessive Agency; BSI M17)

### Process view
- On each model call, which steps follow in fixed order: input check, call, schema validation, plausibility and evidence check, accept or reject? (AIC4 DQ-02 Data Quality Requirements for Operation, structural integrity; BSI M12, M13)
- What happens on invalid output: bounded retry, then fail-closed (no result, visible error) rather than a silent default or a guessed value? (AIC4 DQ-02 Data Quality Requirements for Operation; OWASP LLM01 "Define and validate expected output formats")
- Where does a human review or override a model result, and is the override recorded? Name the roles allowed to do so. (AIC4 PF-09, RE-04 Corrective Measures to the Output; BSI R8 Automation Bias, M20; OWASP LLM09 "Cross-Verification and Human Oversight")
- Are retries, token use, and call latency bounded so a faulty or hostile input cannot cause unbounded cost? (AIC4 RE-03 Monitoring of Model Requests; BSI M15; OWASP LLM10 Unbounded Consumption)
- Is it visible per request which prompt, model version, and settings produced a result, so a run can be reproduced or explained? (AIC4 RE-02 Logging of Model Requests; BSI R7)

### Development view
- Are prompts, schemas, and validators separate modules with their own tests, so the shell can be tested without calling the model? (AIC4 PF-06 Business Testing; BSI M11)
- Is there a versioned reference set ("golden dataset") with expected results, kept apart from any examples placed in prompts? (AIC4 PF-06, DQ-06 Preparation of Training, Validation and Test Data)
- Do tests include adversarial inputs (injected instructions, malformed output, empty output)? (AIC4 SR-05 Testing of Model Robustness; OWASP LLM01 "Conduct adversarial testing and attack simulations")
- Is a change of model, prompt, or parameters a reviewed change that triggers the reference-set run before release? (AIC4 PF-07 Continuous Improvement of Model Performance; BSI M11 "periodisch und anlassbezogen")
- Is the code path that handles untrusted text separated from code that handles trusted data? (AIC4 SR-06; BSI M12)

### Physical view
- Where does the model run (own account, external provider, region), and which data leaves the trust zone with each call? (AIC4 DM-02 Data Access Management; BSI M18; OWASP LLM02 Sensitive Information Disclosure)
- Are API keys for the model service held in a secret store with least privilege and rotation, and is the model endpoint not reachable by end users directly? (AIC4 DM-02; BSI M15 Einschränkung des Zugriffs auf das Modell)
- Are call logs stored where operators cannot alter them, with a defined retention? (AIC4 RE-02, retention of at least three months)
- Is there a fallback or rollback if the provider changes a model, rate-limits, or fails, and is it tested? (AIC4 RE-06 Backup and Disaster Recovery, roll-back of models; PF-02 Monitoring of Performance)

### Scenarios view
- Is there at least one quality scenario "model errs or varies" with a measured value? Examples: share of results that stay the same across n repeated runs on the same input (stability, target stated); share of reference cases answered correctly; share of calls needing a retry; share of runs ending fail-closed. (AIC4 PF-01 Definition of Performance Requirements, sensitivity analysis; PF-02; BSI R7)
- Is there a scenario where the model invents a source or result, and the evidence check rejects it? State the expected detection rate against the reference set. (AIC4 PF-06; BSI R4; OWASP LLM09)
- Is there a scenario where input text contains an instruction ("ignore previous rules") and the decision stays unchanged? (AIC4 SR-05, RE-05 Handling of AI specific Security Incidents; OWASP LLM01; BSI R26, R28)
- Is there a scenario where the provider is down or returns malformed output for every call, and the system stops without a false result? (AIC4 RE-06, PF-02)

## Common mitigations

- **Schema validation** — typed output with strict parsing; anything off-schema is rejected, never repaired by guessing.
- **Bounded retry, then fail-closed** — fixed retry count with the error fed back once; after that, an explicit failure state.
- **Limited context** — the model sees only the material needed for the task, so it has less to invent from and less to leak (OWASP LLM01 "Constrain model behavior"; BSI M14 retrieval-augmented generation).
- **Evidence binding** — each claim carries a verifiable quote or id; claims without verifiable evidence are dropped or flagged.
- **Separation of instructions and data** — untrusted text is marked and delimited, and the model holds no rights beyond its task (BSI M12, M17).
- **Human in the loop** — review for high-impact results, with recorded decisions.
- **Measurement** — reference-set runs, repeated-run stability, retry and failure rates tracked per release and in operation.

## Anti-patterns to flag

- *"We asked the model to answer in JSON, so the format is safe."* A prompt is a request, not a guarantee. Only parsing against a schema is a control.
- *"A temperature of zero makes it deterministic."* It lowers variance but does not remove it, and providers change models. Measure stability.
- *"The prompt tells the model to ignore injected instructions."* An instruction is not a security boundary. OWASP notes it is unclear whether fool-proof prevention exists, so layered controls are needed.
- *"The model checks its own answer."* A second call is also probabilistic. Prefer deterministic checks (schema, rules, quote match) and treat model-on-model review as an additional signal.

## References

- BSI: AI Cloud Service Compliance Criteria Catalogue (AIC4), © 2021 — https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/CloudComputing/AIC4/AI-Cloud-Service-Compliance-Criteria-Catalogue_AIC4.pdf?__blob=publicationFile&v=4
- BSI: Generative KI-Modelle – Chancen und Risiken für Industrie und Behörden, Version 2.0 (17.01.2025); R4 Fehlende Ausgabequalität, R7 Fehlende Reproduzierbarkeit und Erklärbarkeit, R8 Automation Bias, R26 Direkte Manipulationen im Prompt, R28 Indirect Prompt Injections; M11–M20 — https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/KI/Generative_KI-Modelle.pdf?__blob=publicationFile&v=4
- OWASP Top 10 for LLM Applications 2025 (LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM09 Misinformation, LLM10 Unbounded Consumption) — https://genai.owasp.org/llm-top-10/
