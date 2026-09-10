# Privacy, security and responsible AI controls

This document is a control mapping for a pilot, not certification or a completed legal assessment. The deployment owner must verify applicable DPDP provisions and their commencement dates for its actual processing, staffing and contracts. Operational defaults do not establish statutory compliance.

## Threat model

| Threat | Implemented boundary | Residual risk / deployment action |
|---|---|---|
| Cross-account case access | Server-side ownership on every case/document/export/review action | Penetration test and session monitoring |
| CSRF/session theft | Random opaque sessions, hashed tokens, CSRF checks, origin check, HttpOnly cookie, production Secure cookie | HTTPS and secure host required; account recovery not yet implemented |
| Prompt injection | Retrieved content is data, bounded workflow, no model-authorized tools, exact quote checks | Entailment judge can still fail; adversarial and expert review remain necessary |
| Fabricated citation | Model can cite only retrieved IDs; excerpts and source snapshots resolve internally | A real but irrelevant citation requires semantic review |
| Jurisdiction mixing | API source filters and separate graph context | Treaty membership/currentness still depends on reviewed corpus |
| Private upload leakage | Separate case tables/storage; owned-case validation; public retrieval excludes private text | Local Ollama must itself be trusted and locally controlled |
| Unpaid hosted processing of secrets | Explicit cloud opt-in, case/private blocks, confidential flag and sensitive-pattern gate | Pattern detection cannot recognize all sensitive facts; user notice and deployment policy required |
| Translation/voice disclosure | Per-operation consent, confidential gate, Bhashini endpoint allowlist | No live credentials tested; operator must approve terms and processing locations |
| SSRF through ingestion | HTTPS publisher allowlist, public DNS validation, redirect/size/time bounds | Network egress controls are recommended for defense in depth |
| Malicious upload/HTML | PDF/TXT signatures, size limits, extraction handling, HTML snapshots downloaded as attachments | Isolate and patch PDF/OCR dependencies; antivirus scanning is not implemented |
| Exhaustion | Per-session minute limits, daily question cap, bounded context and provider calls | Distributed limits needed before horizontal scaling; auth abuse/email verification need production hardening |
| Unauthorized paid access | Consent scope/expiry/revocation checked server-side; receipts and audits | No actual paid vendor enabled |
| Source drift | Immutable source bytes, review queue, explicit activation, rollback and stale indicators | Human amendment review required; inaccessible sources remain gaps |

## DPDP-oriented processing map

| Processing | Purpose and minimization | Control / owner responsibility |
|---|---|---|
| Guest questions | Answer a question; raw query not stored in audit | Hash and trace metadata retained; session expires after 24 hours |
| Optional accounts | Save and manage cases | Email and Argon2 password hash; account export/deletion |
| Saved cases/private documents | User-requested case workspace | Ownership isolation, explicit upload permission, 90-day inactivity default |
| Facilitator review | User-selected summary and optionally history | Separate immutable submission copy; no automatic external message |
| Bhashini | Requested translation, ASR or TTS | Opt-in, sensitive-data block, no raw-audio persistence |
| Paid connector consent | Enable a named permitted scope | Receipt, purpose, expiry, revocation and access audit |
| Audit/backup | Investigation and recovery | Content-minimized logs; reviewed retention schedule and protected backup storage |

The owner must complete notices, grievance contact, lawful basis/consent wording, processor contracts, rights-handling procedures, child-user policy, applicable transfer restrictions, incident notification procedure and data-retention obligations before public operation. Implementation covers export/delete/withdrawal controls but does not appoint a DPO or certify legal compliance.

The DPDP Rules 2025 have staged commencement: record applicability at the provision level using the official notification. Do not describe every rule as already operative solely because it was published. The acquisition manifest records the official rules resource; qualified review is pending.

## NIST AI RMF and OWASP mapping

- **Govern:** feature-status register, model/corpus versions, role separation, facilitator escalation and release limitations.
- **Map:** explicit jurisdictions, product-category triage, user population, private/public source separation and threat model.
- **Measure:** multilingual scenarios, citation integrity, jurisdiction isolation, abstention tests, observed latency and explicit unmeasured legal accuracy.
- **Manage:** source review, generation gates, bounded calls, provider fallback, rollback and incident response.

OWASP LLM risks are addressed through prompt/data separation, untrusted-output rendering, scoped retrieval, secret isolation and access controls outside the model. These controls are partial risk treatments, not evidence of OWASP or NIST certification.

## External references

- [Official DPDP Rules 2025](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf).
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework).
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/).
- [Gemini API terms](https://ai.google.dev/gemini-api/terms) and [pricing/quotas context](https://ai.google.dev/gemini-api/docs/pricing).

These are implementation references; provider terms and legal applicability must be rechecked when configuring a deployment.
