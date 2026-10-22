# End-to-end validation and publishing

1. Install on your Mac, run pytest and offline evaluation.
2. Set your own API key and run the live OpenAI evaluation; manually review each claim using EVALUATION.md.
3. Build/run Docker; test health, upload, chat, follow-up, sources, errors and workspace deletion.
4. Deploy privately to Cloud Run with your credentials. Repeat actual model requests through deployed UI. Record commit, dependency lock, model, deployment revision and results in reports/VALIDATION.md.
5. Capture screenshots of: upload/index success, cited revenue answer and evidence, multi-turn comparison, missing-forecast refusal. Use only public documents/fictional fixtures and hide keys, accounts and personal information. Put PNGs in docs/screenshots and link them in README. No screenshots are claimed included.
6. Before GitHub publication inspect `git diff --cached` for secrets, private uploads and generated live reports. `.env.example` must contain placeholders only. Add your chosen license (no license is implied by this starter).

```bash
git init
git add .
git diff --cached --stat
git diff --cached
# After inspection:
git commit -m "Build source-grounded financial RAG assistant"
# Create an empty repository in your GitHub account, then:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/financial-insights-rag.git
git push -u origin main
```

GitHub Actions runs offline tests/evaluation without secrets. Do not inject production API keys into pull-request workflows. Publishing to GitHub is a manual step; no repository has been created by this deliverable.
