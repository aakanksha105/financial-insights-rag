# Validation record

Executed October 21, 2026 in Linux x86_64, Python 3.12.14, isolated virtual environment.

- Dependencies installed from package index; exact resolved versions in requirements.txt.
- Editable package installation succeeded; pip check: no broken requirements.
- pytest -q: **17 passed in 1.25s**. Parsing includes generated text PDF, TXT, MD, HTML and CSV; malformed inputs; deterministic chunk limits/IDs; FAISS ranking/cache; embedding errors; valid and invalid citations; follow-up rewrite invocation; abstention/model errors; question/history limits; ranking metrics; Streamlit mocked-provider index/chat/delete flow.
- Streamlit initialization: no AppTest exceptions. Actual HTTP health endpoint on 127.0.0.1:8766 returned `ok`; server was stopped after check.
- Offline fixture evaluation, K=3: Recall@3 1.0, MRR 1.0, four questions, three fictional documents. Keyword test embeddings, not OpenAI; these values are pipeline checks only. Full report: offline.json.

Not executed: live OpenAI requests or semantic/grounded-answer quality evaluation; macOS install; Docker build/run (no Docker executable available); GCP deployment; GitHub publication. No coverage percentage or production latency measured. Streamlit interaction tests use mocked model responses, so they cannot establish real model correctness.

Next validation: follow README local instructions with your key, save live evaluation and human review, test Docker, then privately deploy and repeat UI flow. Update this file only with observed results.

## Subsequent local and cloud validation

- Latest local test run: 29 passed in 1.14 seconds.
- Added calculator regression tests for revenue growth, invalid baselines,
  cited-input validation, explicit million conversions, and mixed-scale rejection.
- Docker build/run and HTTP health check succeeded on the developer's Mac.
- Private Google Cloud Run deployment validated through an authenticated proxy.
- Cloud smoke checks passed for sample revenue retrieval, conversational
  follow-up, Python-calculated growth, and unsupported forecast refusal.
- Microsoft annual-report cloud check returned 14.93% calculated revenue growth
  using cited fiscal 2024 and 2025 figures.
- Fresh-conversation sample calculation accepted 100,000,000 and 120,000,000
  as explicit million conversions and returned 20.00%.
- Earlier live OpenAI retrieval evaluation: Recall@3 1.0 and MRR 0.875
  on four questions over three fictional documents. This is a small fixture,
  not a real-world accuracy benchmark.
- Broad grounded-answer evaluation, load testing, and public access are
  not validated. Deployment remains private.
