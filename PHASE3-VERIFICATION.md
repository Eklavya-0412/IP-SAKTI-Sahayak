# Phase 3 implementation and verification

## Delivered changes

- Development-only trusted origin allowlist for localhost/127.0.0.1 on ports 5173 and 8080, plus PUBLIC_ORIGIN. Production keeps only PUBLIC_ORIGIN. CSRF and cookie checks remain required.
- A shared frontend session bootstrap blocks writes until the token arrives; login rotates tokens and logout clears bootstrap state. Server CSRF tokens are stable across tabs for the same session cookie.
- Page-aware PDF ingestion with 1500-character chunks and 200-character overlap, checksums, reproducible cached extraction, pypdf and page-preserving LlamaParse OCR fallback, pinned multilingual E5 passage embeddings, JSON and pgvector writes, atomic release activation, and graph seeding.
- Existing approved/rejected review decisions are not silently overwritten. Newly imported references are reference_only; draft/notice/form material remains excluded by retrieval eligibility.
- Atomic Tailwind v4 dark slate styling, emerald authority badges, accessible Radix citation drawer, supporting quotes, full excerpts, publisher, locator and official links.
- POST SSE chat with LangGraph stage events, a structured answer event, failure handling and cancellation when switching jurisdiction. Retries retain jurisdiction and market. Local botanical patent query expansion and document diversity prevent manuals from crowding out statutory evidence.
- js-yaml dependency override; npm audit reported zero vulnerabilities during verification.

## Verification achieved

- Frontend production build passed with zero errors. The native Vite config loader avoids the Windows sandbox's esbuild ancestor-directory permission error. Node 22.18+ or Node 24 is recommended for native TypeScript config loading.
- Four frontend transport tests passed (bootstrap concurrency, bootstrap failure/retry, login/logout lifecycle, split UTF-8 SSE).
- Backend tests: **81 passed**, zero failures/errors (one dependency deprecation warning). See docs/phase3-tests.xml for the final backend suite result. The suite includes the original 71 cases plus regression coverage; its total is therefore larger than 71.
- All 18 supplied PDFs were extracted: 2,060 chunks. Scanned pages required OCR. See docs/extraction-verification.json.
- The supplementary FDA and WIPO-hosted amended biodiversity-act PDFs were ingested in the earlier live session: 163 chunks, two versions, an active release and 19 graph links. See docs/benchmark-ingestion-report.json. This is a historical successful execution record, not a fresh post-resume database assertion.
- Live POST /api/v1/questions returned HTTP 200 for all four local origins before corpus activation. Those responses were abstentions with empty evidence; see docs/phase3-pre-ingestion-http.json.
- Offline retrieval over the actual extracted PDFs passes source coverage and isolation for both requested queries; see docs/offline-benchmark.json. This uses SQLite and lexical ranking, not a live pgvector/Groq benchmark.

## Remaining live verification

The interrupted 18-PDF ingestion reached extraction but has no successful commit report. After the workspace change, the sandbox denied outbound Supabase connections (Windows socket error 10013). Full live ingestion, current database counts, and Groq-backed answers with nonempty citations are therefore NOT certified complete. The scripts below finish those steps when run from your normal terminal with network access. No credentials are included in this package.

The FDA PDF is from https://www.fda.gov/files/drugs/published/Botanical-Drug-Development--Guidance-for-Industry.pdf . The manifest's original India Code download returned 404; the biodiversity compilation was acquired from the official WIPO Lex entry at https://www.wipo.int/wipolex/en/legislation/details/23111 . The copy includes the 2023 amendments. Applicability still requires curator review; ingestion does not assert universal NBA approval requirements or approve legal guidance.

## Setup (PowerShell, from this project directory)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt -r backend/requirements-models.txt
Copy-Item .env.example .env
# Edit .env locally: DATABASE_URL, GROQ_API_KEY, GROQ_MODEL,
# SESSION_SECRET, PUBLIC_ORIGIN and optional LLAMA_CLOUD_API_KEY.
# Use GROQ_MODEL=openai/gpt-oss-20b if it is available in your account.
# For local Vite use APP_ENV=development and COOKIE_SECURE=false.
```

Use the same frontend hostname consistently for a browser session. The browser must access the API through the Vite /api proxy; accepting both origins does not make localhost and 127.0.0.1 share cookies.

## Ingest and verify Supabase

```powershell
python scripts/ingest_resources.py --extract-only --report docs/extraction-verification.json
python scripts/ingest_resources.py
python scripts/ingest_resources.py --resources data/benchmark-resources --manifest corpus/benchmark-manifest.json --report docs/benchmark-ingestion-report.json
python scripts/verify_corpus.py --benchmark
```

The release preserves active versions for other sources. Reruns reuse matching versions/chunks and refuse incompatible existing chunk layouts rather than invalidating citations. Vectors are recomputed using the pinned model. The package includes extraction caches and supplementary PDFs; the approximately 470 MB model weights are intentionally excluded and will download on first use. Extraction caches can be removed to force fresh extraction/OCR.

SQL for Supabase SQL Editor:

```sql
SELECT count(*) AS chunks,
       count(vector_embedding) AS non_null_vectors,
       count(*) FILTER (WHERE vector_embedding IS NOT NULL
                         AND vector_dims(vector_embedding) = 384) AS vectors_384
FROM chunks;
SELECT id, name, active, json_array_length(version_ids) AS versions
FROM corpus_releases WHERE active = true;
```

Expected: chunks > 0, non_null_vectors > 0, vectors_384 = non_null_vectors, exactly one active release. The Python verifier additionally checks that the active release contains vectorized chunks and fails on missing benchmark source coverage or scope leakage.

## Start the API and verify POST

```powershell
Set-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, from the project directory:

```powershell
$base = 'http://127.0.0.1:8000/api/v1'
curl.exe -i "$base/health"
curl.exe -sS -c session.cookies "$base/auth/session" -o session.json
$csrf = (Get-Content session.json -Raw | ConvertFrom-Json).csrf_token
'{"query":"Is neem paste patentable under Section 3(p) of the Patents Act?","jurisdiction":"india","market":"treaties","language":"en","previous_questions":[]}' | Set-Content -Encoding ascii question.json
curl.exe -i -b session.cookies -H 'Origin: http://127.0.0.1:5173' -H "X-CSRF-Token: $csrf" -H 'Content-Type: application/json' --data-binary '@question.json' "$base/questions"
curl.exe -N -b session.cookies -H 'Origin: http://localhost:5173' -H "X-CSRF-Token: $csrf" -H 'Content-Type: application/json' --data-binary '@question.json' "$base/questions/stream"
```

Expect HTTP 200 with claims and citations after successful ingestion. HTTP 200 alone does not establish evidence quality. For generated answers to a nonconfidential general question, explicitly add `"cloud_consent":true` to the payload; the default remains local retrieval. A verification failure must abstain rather than emit unsupported claims. `/cases` additionally requires a signed-in account; a guest correctly receives 401 after the CSRF fix.

After starting the backend, `python scripts/verify_api.py` checks HTTP 200, the Answer schema, nonempty claims/citations, citation references and scope. Add `--cloud` to explicitly exercise Groq with the benchmark questions.

## Frontend and tests

```powershell
Set-Location frontend
npm ci
npm run build
npm test
npm run dev
```

If your Windows sandbox blocks esbuild's development dependency optimizer, use the already built application with:

```powershell
npx vite preview --host 127.0.0.1 --port 5173 --configLoader native
```

Backend tests, from backend/:

```powershell
python -m pytest tests
# A sandbox with a restricted shared temp directory can use:
python -m pytest tests --basetemp=../.test-tmp --junitxml=../docs/phase3-tests.xml
```

Offline corpus benchmark, from the project directory:

```powershell
python scripts/benchmark_offline.py
```

Open the chat, switch India/International, choose US, submit the benchmark questions, and inspect source chips. The citation drawer supports Escape and Radix focus trapping. Its badge reflects the actual review status, and a supporting quote is distinct from the complete source excerpt.
