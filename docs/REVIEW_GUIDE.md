# Curator and facilitator guide

## Source curator

Authenticate with a curator or administrator account. Open **Corpus administration**. Review source bytes, extraction quality, original publisher, effective dates, amendment completeness and authority class. Local filenames and government-hosted indexes are not proof of a current consolidated statute. A source may be reference-only even when its publisher is authoritative.

Never approve a draft, consultation notice, statistical report or form as governing law. The UI/API enforce that distinction. Use a specific review note describing provisions checked, version limitations and any OCR recovery. Source approval is a professional responsibility; the software cannot supply the reviewer's expertise.

Enqueue update checks. Inspect failed jobs and publisher errors; do not substitute search snippets for unavailable source text. Create a release selecting one eligible version per source. Record benchmark and review results in its note, activate it, and retain the previous release for rollback.

## Evidence graph

Use the authenticated OpenAPI endpoint `POST /api/v1/admin/graph` with subject, relation, object, evidence chunk ID and reviewed flag. Allowed relations are `defines`, `requires`, `administered_by`, `amends`, `references` and `applies_to`. Read the cited passage before marking an edge reviewed. The graph stores relationships and evidence in PostgreSQL; unreviewed edges do not expand retrieval. No unstated treaty membership or legal obligation should be inferred from a broad overview page.

## Facilitator

Create a facilitator account through the CLI. The **Review desk** shows only shared submissions, not unrestricted access to all private cases. Move a submission through submitted → assigned → in review → resolved. Assignment and resolution require server-enforced roles. Only the assigned reviewer or authorized administrator can advance protected states.

The submitted summary/history is the exact content chosen by the user. Record a response that identifies missing facts, jurisdiction, sources, limitations and recommended next action. Resolution in this application is a workflow state, not a legal certification or a filed application. No communication is sent to third parties automatically.

## Evaluation review

`evals/scenarios.jsonl` includes rubric fields and unreviewed flags. Qualified reviewers should score substantive correctness, responsiveness of citations, safe abstention and language meaning, including negation, quantities, dates and botanical names. Store reviewer role, date, language, source release and notes. Do not promote automated literal-containment scores into legal-accuracy scores. The proposed 95% citation-support and 90% substantive-correctness targets remain unmet until reviewed data establishes them.
