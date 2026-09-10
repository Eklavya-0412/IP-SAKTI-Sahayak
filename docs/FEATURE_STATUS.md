# Feature and integration status

RAG update: semantic retrieval now defaults to enabled; Gemini can plan multiple searches and synthesize eligible reference documents with a **Partial** evidence label. Source review states are preserved. See [RAG_SETUP.md](RAG_SETUP.md) for configuration and the distinction between reference summaries and reviewed guidance. Live Gemini testing awaits the owner's API key.

Status meanings: **implemented** = executable code and a usable route; **credential-required** = adapter exists but no live account test; **external review required** = a qualified person or deployment owner must complete the stated gate. Test evidence is in the generated evaluation and deployment reports.

| Feature | Delivery status | Limitation / completion gate |
|---|---|---|
| Assistant, jurisdiction and market controls | Implemented | India and treaties/US/EU/UK; member-state specifics need country sources |
| Source search/excerpts/citation viewer | Implemented | Reference-only material cannot establish current legal advice |
| PostgreSQL/pgvector and lexical/vector RRF | Implemented | Optional model image/indexing must be enabled; exact configuration shown in capabilities |
| Gemini and Ollama adapters | Credential/model-required | Live generation and entailment quality need evaluation |
| Formulation and ABS assessments | Implemented provisional flows | Rule completeness, legal review and route-specific evidence remain release gates |
| EN/HI/MR interface and questions | Implemented | Legal excerpts remain original; some operational/assessment explanations remain English |
| Bhashini translation, ASR and TTS | Credential-required | Pipeline/language availability, negation and botanical-name fidelity need live testing |
| Accounts, sessions, roles and case ownership | Implemented | Email verification, recovery and production abuse controls need hardening |
| Case save/resume, PDF/JSON and private import | Implemented | Private facts only with local inference; multilingual PDF rendering must be checked |
| Facilitator queue and selected sharing | Implemented | No facilitator staffing or response-time commitment supplied |
| Paid-source scopes/receipts/revocation/audits | Implemented connector boundary | No licensed vendor-specific connector available |
| TKDL and prior-art/registry pointers | Implemented | No restricted data, CAPTCHA bypass or patentability certification |
| Immutable snapshots, checksums and section/page offsets | Implemented | Original local PDFs preserved; source review remains pending |
| OCR and quality flags | Implemented optional recovery | Damaged/scanned pages require visual review; existing citations preserved |
| Source update worker, review, releases and rollback | Implemented | Regression review is an operator procedure, not automatic legal approval |
| Relational evidence graph and bounded LangGraph | Implemented | Curated legal relationships require review; no unrestricted agent tools |
| Privacy, audit, retention and account rights controls | Implemented pilot controls | DPDP/legal, threat-model and deployment review not complete |
| Docker, migrations, reverse proxy and health | Implemented | See actual rehearsal results; TLS requires deployment configuration |
| Backup/restore scripts | Implemented | Operator must schedule encrypted backups and expiry |
| 123 substantive trilingual scenarios + adversarial set | Implemented and executable | Templated families; qualified legal/language scoring pending |
| Report, presentation, diagrams, guides and demo script | Submission artifacts | Read the measured-results and limitations sections |

No integration is labelled credential-tested merely because its code compiles. No expert accuracy threshold is claimed met without an identified reviewer and scored sample. Public launch and hosting purchase are excluded.
