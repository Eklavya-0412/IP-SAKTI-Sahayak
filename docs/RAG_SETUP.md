# Vector retrieval and Gemini synthesis

## Repeated-run failure audit

Two further live runs are recorded in `repeated-classification-test.json`. Run 1 resolved four draft citations and accepted three entries in 59.086 seconds. Run 2 resolved three draft citations but Gemini returned HTTP 429 during verification; it correctly released no answer. These results do not establish reliable completion of every part of the user's question. Provider quota and verification quality remain limitations.

The model can now select `support_id`; the server resolves the original passage, while a separate entailment check remains mandatory. Traces expose counts for drafted, resolved and verified claims, without storing raw provider responses. Once generation has been attempted, an unsuccessful draft or provider call results in abstention, not unverified excerpt substitution. Explicit no-generation/source-search mode remains available. All 71 backend tests passed after this change. This policy supersedes earlier descriptions of falling back to excerpts following failed generation.

## Clarification-answer regression

The exact oral-herbal-product question was rerun with Gemini after adding separate `explanation` and `clarification` claim kinds. It returned a regulatory/patent distinction and two evidence-backed clarification questions in 63.145 seconds. See `classification-live-test.json`. This demonstrates both parts of that request, not completeness of a licensing assessment. The verifier now evaluates whether clarification questions follow from source distinctions instead of requiring questions to be quoted statutory assertions. The frontend labels clarification questions separately, filters empty limitation strings and keeps limitations visible. Injectables-specific fallback sentences are excluded for explicitly oral questions; short incomplete fragments are suppressed. The production build and 69 backend tests passed.

## Live validation update

The owner's key was tested successfully. Google returned HTTP 404 for `gemini-2.5-flash`, stating it was unavailable to new users and recommending `gemini-3.6-flash`. The configured/default model is now `gemini-3.6-flash`. The full live test planned three searches, retrieved eight chunks, drafted four claims and accepted three after verification. Total time was 78.797 seconds, including local retrieval/model initialization. Citation IDs, literal support spans and India scope passed mechanical checks. The result remains Partial because source applicability is unreviewed. See [gemini-live-test.json](gemini-live-test.json); this is one live sample, not an accuracy benchmark.

PDF quote handling now resolves whitespace-normalized quotations back to exact original spans without changing words or negation. Gemini 3 requests use a low thinking level, an 8,192-token output ceiling and a 90-second per-request timeout. These settings follow the [official Gemini thinking API documentation](https://ai.google.dev/gemini-api/docs/generate-content/thinking), accessed 6 September 2026. Incomplete output is rejected, and model HTTP failures display a specific safe explanation without leaking keys.

The assistant does not look up predefined answers. It searches document chunks and, when configured, asks an LLM to synthesize and verify the evidence. The earlier preview was operating as an excerpt search: embeddings were disabled and generation had no provider. The guided classification and ABS questionnaires are separate rule-based workflows.

## Updated question pipeline

1. Validate the selected jurisdiction, session and privacy settings.
2. Gemini rewrites the question and up to four prior user questions into bounded standalone searches. Prior assistant responses are not treated as evidence.
3. Encode searches with pinned multilingual E5-small. Search the persisted chunk embeddings and lexical/full-text indexes within the selected jurisdiction and active corpus release.
4. Fuse ranks across searches and limit repeated chunks from one document. Expand reviewed graph evidence within the same scope.
5. Send the actual retrieved text, locators, authority types and review status to Gemini 2.5 Flash. Ask for an explanation responsive to the user, with database citation IDs and exact support quotes.
6. Reject invented IDs/quotes and run a separate entailment check. Release accepted claims with citations; otherwise show clearly labelled excerpts or abstain.

PostgreSQL deployment uses pgvector with 384-dimensional vectors and HNSW/GIN indexes. Local SQLite development stores the same vectors as arrays and computes similarity in Python; it is not the production vector index. The existing local corpus has 9,305 embedded chunks. New ingestion must be followed by embedding before its chunks participate in dense retrieval.

## Configure local development

The ignored root `.env` has been prepared for this workspace. Set `GEMINI_API_KEY` locally; do not commit it or paste it in chat. Its relevant settings are:

```dotenv
GENERATION_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your-local-key
EMBEDDINGS_ENABLED=true
REFERENCE_SYNTHESIS_ENABLED=true
```

Restart the API after changing settings. Enable the question's cloud-processing checkbox for a general public question. Confidential questions and private case history remain blocked from Gemini, including the search-planning call.

```powershell
.venv\Scripts\python -m pip install -r backend/requirements-models.txt
.venv\Scripts\python scripts/index_embeddings.py
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For Docker, set `INCLUDE_MODELS=true` and `EMBEDDINGS_ENABLED=true` in the deployment environment, rebuild, ingest the corpus and run `python -m app.cli embed` in the API container. Keep the existing Docker database/storage configuration; do not copy the local SQLite environment into the container.

## Reference summaries versus reviewed guidance

`REFERENCE_SYNTHESIS_ENABLED=true` allows the LLM to explain what eligible reference documents say without marking them expert-approved. These answers remain **Partial**, retain source-review warnings and must not claim verified current-law applicability. Drafts, forms, statistics, rejected/pending versions and out-of-scope sources are still excluded by retrieval. Set this flag to `false` to restrict generation to approved, non-stale evidence.

No legal-review status is automatically changed to make generation work. The reference-summary policy supersedes the original documents' statement that all generation always requires approved sources.

## What to inspect

- The composer displays the configured model or explicitly says that the LLM is not configured.
- Answer JSON reports `retrieval`, `query_count`, `distinct_sources`, `llm_query_planning`, `generation_provider` and `generation_model`.
- `mode=generated` means claims passed the configured generation checks. `mode=retrieval` means literal excerpts, not a generated answer.
- Credentials present is not the same as a successful provider call. A live Gemini result cannot be validated until the owner configures the key.
- Tests mock provider responses to validate orchestration and confidentiality; these are not model-quality scores. Existing evaluation reports describe the earlier baseline until explicitly rerun.

Relevant code: `backend/app/retrieval.py`, `providers.py`, `assistant.py`, `schemas.py`, and `frontend/src/App.tsx`.
