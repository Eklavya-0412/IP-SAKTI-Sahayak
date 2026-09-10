# Final validation — 6 September 2026

## Subsequent RAG improvement

The assistant now includes Gemini query planning, bounded previous-question context, multi-query rank fusion and citation-checked reference synthesis. A real local corpus query returned eight hybrid-search chunks from five documents with embeddings enabled and no embedding error. All 9,305 stored chunks have embeddings. This cold-process check took 40.86 seconds including model initialization; it is not a warm-query latency claim. Frontend production build passed. Four new mocked-provider regression tests passed; a live Gemini answer remains untested until an API key is configured. The historical evaluation figures below describe the preceding excerpt-search baseline.

- Backend: 63 tests passed; detailed JUnit results are in `test-results.xml`.
- Frontend: OpenAPI types regenerated; TypeScript and Vite production build passed (1,642 modules).
- Browser: Marathi classification advanced from intended use to the food-reference question; restart returned to question 1. The assessment displays India scope. English assistant restored for handoff.
- Evaluation: 381 baseline executions and a separate 36-execution local semantic sample are recorded. Citation resolution and scope isolation are mechanical checks; qualified substantive correctness and language quality are unmeasured.
- Artifacts: report rendered and visually inspected; 14-slide editable PowerPoint has structural validation in `presentation-validation.json`. Native Microsoft PowerPoint was not used for verification.
- Deployment: the earlier Docker/PostgreSQL and isolated backup/restore rehearsal is recorded in `deployment-results.json`. Docker Desktop became unavailable later in the session, so the final incremental changes were checked locally rather than rebuilt and rehearsed in Docker. Run the documented rehearsal again before deployment.
- Integrations: no live Gemini/Bhashini credentials, paid subscriptions, facilitator staffing or qualified legal/language reviewers were supplied. No source version has been expert-approved for generated current-law guidance.

The source package excludes credentials, database content, private uploads, downloaded models and remote snapshots. Rebuild the corpus with the supplied manifest and acquisition commands; inaccessible sources remain explicit coverage gaps.
