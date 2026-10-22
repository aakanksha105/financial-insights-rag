# Grounded-answer evaluation protocol

Run the OpenAI evaluation command in README to capture question, expected facts, answer, and supplied evidence. Preserve model IDs, dependency lock, prompt revision (git SHA), corpus hashes, date and K in your experiment notes. Never mix offline and live results.

For each claim, manually mark: supported / contradicted / not supported. Check every number, currency, fiscal period, company, and causal statement against the cited excerpt and original document. Inspect explanation separately for uncited factual additions. Record citation validity, citation entailment, answer correctness, completeness, and appropriate abstention. A valid ID alone is not support.

Use `human_review` in each generated report row to record reviewer, claim labels, notes, and decision. Define claim support rate as supported factual claims divided by all factual claims (including explanations). Mark denominator-zero answers N/A, not 100%. Define abstention accuracy over explicitly labeled answerable/unanswerable questions. Have a second reviewer independently score at least a subset and adjudicate disagreements. Do not use the same generating model as the only judge.

Before any quality claim, replace/extend fixtures with permissioned real reports: at least 30 labeled questions across companies, periods, currencies, table-heavy pages, news and unanswerable questions. Freeze a held-out set before tuning prompts/chunks. Include follow-up conversations and prompt injection documents. Record retrieval failures separately from generation errors. Measure API usage and latency around full requests with a monotonic clock if needed; this project does not claim those measurements.

Acceptance for manual end-to-end smoke check: cited chunks must exist, reported numbers must match source units/period, follow-up must retain company, unsupported forecasts must be refused, and API errors must leave the workspace usable. A failed criterion blocks publication as validated.
