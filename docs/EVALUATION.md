# Evaluation report

Generated from actual executions; no simulated results.

Corpus release tested: `bf0d4eed-bd6a-4325-91ef-06294ec312ed`.
Automated backend tests: 63; failures: 0; errors: 0.
Docker/restore rehearsal: **passed**. Details: `docs/deployment-results.json`.

| Language | Executions | Retrieval / abstention | Citation resolution | Scope isolation | p50 / p95 ms |
|---|---:|---|---:|---:|---:|
| en | 127 | 117 / 10 | 100% | 100% | 377 / 642 |
| hi | 127 | 99 / 28 | 100% | 100% | 376 / 635 |
| mr | 127 | 105 / 22 | 100% | 100% | 382 / 747 |

## What these results establish

Returned chunk IDs resolve, original excerpts retain literal integrity, and returned citations stay within the selected jurisdiction/market. An abstention has no citations and therefore vacuously passes these mechanical checks; response counts must be considered. The adversarial set has only four scenarios per language, so 100% on that small set does not establish general safe-abstention accuracy.

## Unmeasured gates

Qualified substantive correctness, genuine citation relevance/entailment, complete safe-abstention accuracy, legal translation quality, and live voice quality remain **unmeasured**. The proposed 95% citation-support and 90% legal-correctness gates are not claimed met. Zero expert-reviewed scenarios are currently recorded. Source-only execution consumes no generation API tokens; hosted latency, quota and cost are not inferred from local timings.

## Reproduction

Run `python scripts/build_evaluation.py` then `python scripts/evaluate.py` using the same snapshot release. This dataset contains 123 substantive scenarios (41 topics × 3 evidence tasks), each in English/Hindi/Marathi, plus four adversarial scenarios in each language: 381 executions. Questions are templated families and need independent expert expansion. The runner saves per-execution trace IDs, citation IDs, modes, timings and null human scores.

## Hardware and conditions

```json
{
  "platform": "Windows-11-10.0.26200-SP0",
  "processor": "Intel64 Family 6 Model 197 Stepping 2, GenuineIntel",
  "python": "3.13.6"
}
```

Sequential actual-corpus calls; source-only mode. No paid tokens or model-generated answers.

The evaluator is sequential; HTTP concurrency, semantic-model latency and remote-provider performance require separate measurements. Run the deployment rehearsal for PostgreSQL/HTTP verification. Raw results: `evals/results/latest.json`; tests: `docs/test-results.xml`.

## Local semantic-retrieval sample

A separate 36-execution sample used the pinned, downloaded E5 model. Trace records show {'hybrid': 28, 'lexical': 0, 'null': 8}. These are actual retrieval modes; pre-retrieval abstentions have no retrieval mode. Source coverage and relevance still require expert review.

| Language | Sample n | p50 / p95 ms |
|---|---:|---:|
| en | 12 | 2788 / 3212 |
| hi | 12 | 2739 / 8973 |
| mr | 12 | 2772 / 2946 |
