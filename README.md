# IP-SAKTI Sahayak

Classification terminology reference: [CDSCO traditional-drugs definitions](https://www.cdsco.gov.in/opencms/opencms/en/Traditional_Drugs/) and [India Code Drugs and Cosmetics Act compilation](https://www.indiacode.nic.in/bitstream/123456789/6800/1/drug_and_conmetic_act_1940.pdf), consulted 6 September 2026 to distinguish the regulatory definition in section 3(h)(i) from patent-grant status. This review does not approve corpus versions or establish amendment completeness.

**Gemini live test passed:** the available model is now `gemini-3.6-flash`; `gemini-2.5-flash` returned an account-availability error. See [recorded live RAG test](docs/gemini-live-test.json) and [setup details](docs/RAG_SETUP.md). Provider implementation reference: [Google's thinking configuration documentation](https://ai.google.dev/gemini-api/docs/generate-content/thinking), accessed 6 September 2026, used for Gemini 3 response settings.

**RAG update:** [Vector retrieval and Gemini setup](docs/RAG_SETUP.md) explains the enabled embedding path, LLM search planning, follow-up context and citation-checked reference synthesis. This supersedes the original approved-only generation description below; historical evaluation reports remain labelled baseline results.

A deployable pilot for source-grounded Ayurveda intellectual-property and regulatory information. English, Hindi and Marathi interface; visibly separate India and international contexts; US, EU and UK market selectors. **Information, not legal advice.**

The default installation works without API keys: it searches the reference library and shows original source excerpts. It does not present these as a synthesized legal opinion. Current-law approval, expert evaluation and live provider credentials are explicit release dependencies.

## Run with Docker

Read the [module and feature guide](docs/MODULES_AND_FEATURES.md) for real-life examples, technical workflows, per-module technologies, code locations and implementation gaps.

Submission downloads: [source and submission ZIP](deliverables/IP-SAKTI-Source-and-Submission.zip), [project report PDF](deliverables/IP-SAKTI-Project-Report.pdf), and [14-slide PowerPoint](deliverables/IP-SAKTI-Submission-20260906.pptx). The archive includes a per-file checksum manifest, the original Resources, and reproducible acquisition scripts. Credentials, private runtime data, downloaded model weights and remote source snapshots are excluded.

See [final validation notes](docs/FINAL_VALIDATION.md) and [feature status](docs/FEATURE_STATUS.md) for the measured checks and remaining release gates.

Requires Docker Desktop / Docker Engine with Compose, Python 3.12+ for configuration, and enough disk space for images and source snapshots. Semantic embeddings require additional model download and memory.

```powershell
python scripts/configure.py
docker compose up -d --build
docker compose exec api python -m app.cli ingest
docker compose exec api python -m app.cli ingest --remote --pending
docker compose exec api python -m app.cli reference-release
```

Open **http://localhost:8080**. API documentation: **http://localhost:8080/docs** (or `/api/v1` routes documented in `docs/openapi.json`). Use the exact configured `PUBLIC_ORIGIN`; another hostname is a different origin. Do not use a development cookie configuration for public deployment.

This workspace also has a separate Docker rehearsal configuration, `.env.docker`, and a local development preview at **http://127.0.0.1:5173**. Rehearsal commands use `docker compose --env-file .env.docker ...`. The generated configuration contains secrets and is intentionally excluded from source control.

Create an administrator interactively:

```powershell
docker compose exec api python -m app.cli create-user --email curator@example.org --role admin
```

Sign in through the application. No default account or password is shipped. Source review, release activation and graph editing require curator/admin authorization. A facilitator account is created with `--role facilitator`.

## Development and checks

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
cd backend
..\.venv\Scripts\python -m alembic upgrade head
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal:
cd frontend
npm ci
npm run dev
```

Without `.env`, development defaults to SQLite under `data/`. For a local process alongside Docker, use `.env.docker` only for Compose so its database hostname does not override local defaults. PostgreSQL is the production retrieval database; SQLite is a development fallback.

```powershell
cd backend
..\.venv\Scripts\python -m pytest tests -q
cd ..
.venv\Scripts\python scripts/export_openapi.py
cd frontend
npm run types:api
npm run build
cd ..
.venv\Scripts\python scripts/build_evaluation.py
.venv\Scripts\python scripts/evaluate.py
.venv\Scripts\python scripts/build_submission.py
```

## Architecture and integrations

React/TypeScript/Vite with Tailwind and Radix-based Shadcn primitives; FastAPI/Pydantic/SQLAlchemy/Alembic; PostgreSQL/pgvector; LangGraph; PostgreSQL job worker; immutable filesystem snapshots; Nginx reverse proxy. No mandatory paid embedding or database subscription.

- **Generation:** `GENERATION_PROVIDER=gemini`, a `GEMINI_API_KEY`, and the configurable `GEMINI_MODEL=gemini-2.5-flash`; or `GENERATION_PROVIDER=ollama` with a reachable local endpoint. Only curator-approved, nonstale sources can support generated claims. Free Gemini requires explicit per-query cloud opt-in and excludes cases/private content. Availability and quotas are deployment constraints.
- **Embeddings:** set `INCLUDE_MODELS=true`, `EMBEDDINGS_ENABLED=true` and the pinned revision in `.env.example`; rebuild, then run `docker compose exec api python -m app.cli embed`. CPU PyTorch is installed in that build. Local development can install `backend/requirements-models.txt` and run `scripts/index_embeddings.py`.
- **Language/voice:** Bhashini requires user ID, API key and pipeline ID. The adapter discovers language services, requests consent, supports transcript correction, and reports outages. Unconfigured services remain visibly unavailable. Legal excerpts retain their original text.
- **Paid sources:** scoped consent, receipts, revocation, access auditing and a connector boundary are implemented. No vendor connector is claimed live. TKDL and restricted registries use lawful public pointers/manual handoffs.

## Deliverables and release status

See [feature status](docs/FEATURE_STATUS.md), [measured evaluation](docs/EVALUATION.md), [coverage matrix](corpus/coverage.md), [project report](docs/PROJECT_REPORT.md), [architecture](docs/ARCHITECTURE.md), [operations](docs/OPERATIONS.md), [security and privacy](docs/SECURITY.md), [user guide](docs/USER_GUIDE.md), [curator/facilitator guide](docs/REVIEW_GUIDE.md), and [demo script](docs/DEMO_SCRIPT.md).

The source registry is [corpus/manifest.json](corpus/manifest.json). The content-based inventory and acquisition evidence are generated from actual source versions. The 18 supplied PDFs remain unchanged in `Resources/`. A source's presence in the manifest does not mean it was acquired, extracted successfully, or approved as current law. No expert legal review, certification, vendor subscription or public launch is implied.

## Resource bibliography

The following section is generated by `scripts/build_submission.py` from the manifest and acquired snapshots. It records every acquired source and separately lists excluded, inaccessible, procedural, and pointer-only resources. Do not edit the generated section manually.

<!-- BIBLIOGRAPHY:START -->
### Acquired sources

Acquisition dates and hashes are in `corpus/inventory.json`. “Reference only” does not mean approved current law.
- [Patents Act, 1970](https://ipindia.gov.in/) — IP India; legislation; purpose: patents; accessed 2026-09-06; reference_only, 484 chunks. Supplied file: `Resources/patent_act_1970.pdf`. Supplied compilation; amendment completeness must be checked.
- [Manual of Patent Office Practice and Procedure](https://ipindia.gov.in/) — IP India; guidance; purpose: patents; accessed 2026-09-06; reference_only, 595 chunks. Supplied file: `Resources/manual of patent office.pdf`. Practice guidance; subsequent rules prevail.
- [Guidelines for Examination of Ayush Related Inventions, 2025](https://ipindia.gov.in/) — IP India; guidance; purpose: patents; accessed 2026-09-06; reference_only, 57 chunks. Supplied file: `Resources/guidelines_ayush related inventions.pdf`. 2025 guideline verified by visual inspection of supplied cover. Text extraction has spaced glyphs.
- [Pharmaceutical Patent Examination Guidelines, 2014](https://ipindia.gov.in/) — IP India; guidance; purpose: patents; accessed 2026-09-06; reference_only, 116 chunks. Supplied file: `Resources/guidelines-pharma.pdf`. Historical guidance; assess amendments and later guidance.
- [Guidelines: Traditional Knowledge and Biological Material](https://ipindia.gov.in/) — IP India; guidance; purpose: traditional knowledge; accessed 2026-09-06; reference_only, 36 chunks. Supplied file: `Resources/guidelines for processing patent application.pdf`. Useful TK and biological material context; verify current ABS provisions.
- [Patent Search and Examination Guidelines, 2015](https://ipindia.gov.in/) — IP India; guidance; purpose: patents; accessed 2026-09-06; reference_only, 274 chunks. Supplied file: `Resources/guideline-search&examination.pdf`. Practice reference; not a current consolidated rulebook.
- [Geographical Indications Act, 1999](https://ipindia.gov.in/) — IP India; legislation; purpose: gi; accessed 2026-09-06; reference_only, 128 chunks. Supplied file: `Resources/geog_indiciations 1999.pdf`. Supplied Gazette; verify amendments.
- [Geographical Indications Rules, 2002](https://ipindia.gov.in/) — IP India; legislation; purpose: gi; accessed 2026-09-06; reference_only, 276 chunks. Supplied file: `Resources/geo_indication_rules_2002.pdf`. Base rules; read with subsequent amendments.
- [Geographical Indications Amendment Rules, 2025](https://ipindia.gov.in/) — IP India; legislation; purpose: gi; accessed 2026-09-06; reference_only, 21 chunks. Supplied file: `Resources/geo_indication_rules_2025.pdf`. Gazette dated 3 November 2025, G.S.R. 812(E).
- [GI Practice and Procedure Manual, 2011](https://ipindia.gov.in/) — IP India; guidance; purpose: gi; accessed 2026-09-06; reference_only, 213 chunks. Supplied file: `Resources/geo_indi_practice_manual.pdf`. Historical procedural guidance.
- [Trade Marks Act, 1999 (Hindi)](https://ipindia.gov.in/) — IP India; legislation; purpose: trademarks; accessed 2026-09-06; reference_only, 223 chunks. Supplied file: `Resources/trades_act_1999.pdf`. Hindi supplied text; extraction and amendment verification required.
- [Trade Marks Rules, 2017](https://ipindia.gov.in/) — IP India; legislation; purpose: trademarks; accessed 2026-09-06; reference_only, 486 chunks. Supplied file: `Resources/trades_rules_2017.pdf`. Bilingual Gazette; some glyph extraction is damaged.
- [Designs Rules, 2001](https://ipindia.gov.in/) — IP India; legislation; purpose: designs; accessed 2026-09-06; reference_only, 129 chunks. Supplied file: `Resources/design rules_2001.pdf`. Mixed scanned/text pages require selective OCR; verify amendments.
- [Manual of Designs Practice and Procedure](https://ipindia.gov.in/) — IP India; guidance; purpose: designs; accessed 2026-09-06; reference_only, 167 chunks. Supplied file: `Resources/designmanuak.pdf`. Office guidance; verify against current statute and rules.
- [Patent Form 1: Application for Grant](https://ipindia.gov.in/) — IP India; form; purpose: forms; accessed 2026-09-06; reference_only, 16 chunks. Supplied file: `Resources/form1-appl for grant of patent.pdf`. Form resource only. Verify latest official form before use.
- [Patent Form 3: Section 8 Statement and Undertaking](https://ipindia.gov.in/) — IP India; form; purpose: forms; accessed 2026-09-06; reference_only, 6 chunks. Supplied file: `Resources/undertaking form.pdf`. Potential legacy form; current-rule verification required.
- [PCT Legal Texts](https://www.wipo.int/en/web/pct-system/texts/index) — WIPO; guidance; purpose: pct; accessed 2026-09-06; reference_only, 5 chunks. Official index includes version-specific texts. Index is navigation; ingest linked instruments separately.
- [ISA and IPEA Agreements](https://www.wipo.int/en/web/pct-system/access/isa_ipea_agreements) — WIPO; guidance; purpose: pct; accessed 2026-09-06; reference_only, 4 chunks. Authority-specific agreements and access links.
- [Drugs and Cosmetics Act and Rules (through December 2016)](https://cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Ethics-Committee/Guideline-Document/Drugs_CosmeticsAct1940_Rules1945.pdf) — CDSCO; legislation; purpose: classification; accessed 2026-09-06; reference_only, 2851 chunks. Historical compilation through 31 December 2016. Current obligations need later amendments.
- [Ayurveda Aahara Category A Recipes, July 2025](https://fssai.gov.in/docs/food-law/advisory/68835f872eaf4Order%20dated%2025-07-2025%20enclosing%20Ayurveda%20Aahara.pdf) — FSSAI; order; purpose: aahara; accessed 2026-09-06; reference_only, 3 chunks. Supplied URL; fetch must succeed before indexing.
- [Ayurveda Aahara Recipes Part 2, June 2026](https://fssai.gov.in/docs/food-law/advisory/6a34f644db631Annexure%20No_part-2%20Compendium%20of%20Ayurveda%20Aahara%20recipes.pdf) — FSSAI; order; purpose: aahara; accessed 2026-09-06; reference_only, 596 chunks. Supplied URL; official advisory listing identifies 19 June 2026 update.
- [New and Extant Plant Variety Application](https://plantauthority.gov.in/sites/default/files/newextantvariety2013.pdf) — PPV&FR Authority; form; purpose: plant varieties; accessed 2026-09-06; reference_only, 53 chunks. Form, not the governing plant-variety statute.
- [Pharmaceutical Patents Granted: Historical List](https://ipindia.gov.in/uploads/dynamic-tables/1778068157_patentGranted_Pharma_2010-11_Jul2013%20(1).pdf) — IP India; registry; purpose: prior art; accessed 2026-09-06; reference_only, 89 chunks. Historical grants; individual records and current status require independent verification.
- [India ABS Regulations 2025: National Record](https://absch.cbd.int/en/database/MSR/ABSCH-MSR-IN-283500/1) — CBD ABS Clearing-House / India; guidance; purpose: abs; accessed 2026-09-06; reference_only, 1 chunks. Government-submitted record and source-document links. Dynamic text may require manual capture.
- [National Biodiversity Authority FAQs](https://www.nbaindia.nic.in/index.php/about-us/faqs) — NBA; guidance; purpose: abs; accessed 2026-09-06; reference_only, 30 chunks. Official explanatory guidance; governing provisions take precedence.
- [NBA FAQs: IP and access obligations](https://www.nbaindia.nic.in/about-us/faqs?page=1) — NBA; guidance; purpose: abs; accessed 2026-09-06; reference_only, 29 chunks. 
- [NBA FAQs: ABS regulations and commencement](https://www.nbaindia.nic.in/about-us/faqs?page=3) — NBA; guidance; purpose: abs; accessed 2026-09-06; reference_only, 27 chunks. 
- [WIPO GRATK Treaty Summary](https://www.wipo.int/en/web/treaties/ip/gratk/summary_gratk) — WIPO; guidance; purpose: gratk; accessed 2026-09-06; reference_only, 6 chunks. Summary; do not equate adoption with entry into force or applicability to a particular state.
- [WIPO GRATK Treaty Text](https://www.wipo.int/wipolex/en/text/593055) — WIPO; treaty; purpose: gratk; accessed 2026-09-06; reference_only, 32 chunks. 
- [TRIPS Agreement: Legal Text](https://www.wto.org/english/docs_e/legal_e/27-trips_01_e.htm) — WTO; treaty; purpose: trips; accessed 2026-09-06; reference_only, 2 chunks. 
- [Madrid System](https://www.wipo.int/en/web/madrid-system) — WIPO; guidance; purpose: madrid; accessed 2026-09-06; reference_only, 9 chunks. Official navigation and system overview; eligibility is country-specific.
- [Hague System](https://www.wipo.int/en/web/hague-system) — WIPO; guidance; purpose: hague; accessed 2026-09-06; reference_only, 7 chunks. Official navigation; membership must be checked for applicant and designated markets.
- [Budapest Treaty System](https://www.wipo.int/en/web/budapest-system) — WIPO; guidance; purpose: budapest; accessed 2026-09-06; reference_only, 9 chunks. 
- [Botanical Drug Development Guidance for Industry](https://www.fda.gov/files/drugs/published/Botanical-Drug-Development--Guidance-for-Industry.pdf) — US FDA; guidance; purpose: market access; accessed 2026-09-06; reference_only, 105 chunks. Guidance document; distinguish enforceable regulations from recommendations.
- [Dietary Supplements: Information for Industry](https://www.fda.gov/food/dietary-supplements/information-industry-dietary-supplements) — US FDA; guidance; purpose: market access; accessed 2026-09-06; reference_only, 2 chunks. 
- [Herbal Medicinal Products: EU Framework](https://www.ema.europa.eu/en/human-regulatory-overview/herbal-medicinal-products) — EMA; guidance; purpose: market access; accessed 2026-09-06; reference_only, 4 chunks. EU common framework; national competent-authority requirements need country selection.
- [Apply for a Traditional Herbal Registration](https://www.gov.uk/guidance/apply-for-a-traditional-herbal-registration-thr) — MHRA / GOV.UK; guidance; purpose: market access; accessed 2026-09-06; reference_only, 5 chunks. 
- [Digital Personal Data Protection Rules, 2025](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf) — MeitY; legislation; purpose: privacy; accessed 2026-09-06; reference_only, 200 chunks. Read with commencement notifications. No blanket compliance certification implied.
- [WIPO Copyright Overview](https://www.wipo.int/en/web/copyright) — WIPO; guidance; purpose: copyright; accessed 2026-09-06; reference_only, 9 chunks. International overview; Indian statutory corpus remains a tracked gap until official Act acquired.
- [WIPO Trade Secrets](https://www.wipo.int/en/web/trade-secrets) — WIPO; guidance; purpose: trade secrets; accessed 2026-09-06; reference_only, 13 chunks. Overview; India-specific contractual and case-law guidance needs Indian authority.
- [Copyright Act, 1957](https://www.indiacode.nic.in/indiacode/bitstream/123456789/1367/1/A195714.pdf) — India Code; legislation; purpose: copyright; accessed 2026-09-06; reference_only, 317 chunks. Official compilation; amendment applicability review pending.
- [Designs Act, 2000](https://www.indiacode.nic.in/indiacode/bitstream/123456789/1917/1/A2000-16.pdf) — India Code; legislation; purpose: designs; accessed 2026-09-06; reference_only, 85 chunks. 
- [Protection of Plant Varieties and Farmers Rights Act, 2001](https://plantauthority.gov.in/sites/default/files/ppvfract2001.pdf) — India Code; legislation; purpose: plant varieties; accessed 2026-09-06; reference_only, 166 chunks. 
- [Biological Diversity Rules, 2024](https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/IA_DOCS/1010_11082025024835.pdf) — MoEFCC / PARIVESH; legislation; purpose: abs; accessed 2026-09-06; reference_only, 238 chunks. Official Gazette copy. Verify later amendments before advice.
- [Patent Rules and Amendments: official index](https://ipindia.gov.in/resource/patents-resources-rules) — IP India; guidance; purpose: patents; accessed 2026-09-06; reference_only, 3 chunks. Links to rules consolidated through 15 March 2024 and second amendment 16 March 2024. Draft entries must not support answers.
- [Patents Amendment Rules, 15 March 2024](https://ipindia.gov.in/storage/uploads/docs-operator/17e7b633-4b6f-4737-9408-8c8fe72c9cfc.pdf) — IP India; legislation; purpose: patents; accessed 2026-09-06; reference_only, 278 chunks. Gazette linked by official rules index, accessed September 2026.
- [Patents Second Amendment Rules, 16 March 2024](https://ipindia.gov.in/storage/uploads/docs-operator/33524c6c-73dd-4fe0-bbd7-43c8f187413e.pdf) — IP India; legislation; purpose: patents; accessed 2026-09-06; reference_only, 31 chunks. 
- [Patent Cooperation Treaty text](https://www.wipo.int/documents/d/pct-system/docs-en-texts-pct.pdf) — WIPO; treaty; purpose: pct; accessed 2026-09-06; reference_only, 156 chunks. Treaty text linked by official PCT legal texts index; separate from implementing regulations.
- [PCT Regulations effective January 2026](https://www.wipo.int/documents/d/pct-system/docs-en-texts-pct-regs2026.pdf) — WIPO; treaty; purpose: pct; accessed 2026-09-06; reference_only, 644 chunks. Version-specific official regulations; verify effective-date cover.

### Disposition register

These supplied/registered resources are excluded, unavailable, background, or access pointers. They cannot support legal conclusions merely because they are listed.
- [Draft GI and GI Logo Guidelines, October 2025](https://ipindia.gov.in/) — excluded. DRAFT: excluded from substantive answer context.
- [Public notice inviting comments on draft trade mark manual, 2015](https://ipindia.gov.in/) — excluded. One-page scanned consultation notice, not the manual. Excluded.
- [World Intellectual Property Indicators 2025](https://www.wipo.int/edocs/pubdocs/en/wipo-pub-941-17-2025-en-world-intellectual-property-indicators-2025.pdf) — background. Background statistics only; CC BY 4.0 attribution required. Not governing law.
- [Ayurveda Aahara Kind of Business Order, 1 September 2025](https://www.fssai.gov.in/upload/advisories/2025/09/68b67efa6f47520250902103601289.pdf) — acquired but no usable extracted passages. Official alternate URL found after supplied link failed.
- [Convention on Biological Diversity: Text](https://www.cbd.int/convention/text) — acquired but no usable extracted passages. 
- [Nagoya Protocol: Text and Annex](https://www.cbd.int/abs/text) — acquired but no usable extracted passages. 
- [Traditional Knowledge Digital Library](https://www.tkdl.res.in/) — pointer. Public information and lawful access pointer. No automated restricted-database access.
- [Pharmacopoeia Commission for Indian Medicine and Homoeopathy](https://pcimh.gov.in/) — pointer. Standards source directory. Ingest individual publications only after checking rights and version.
- [Biological Diversity Act, 2002 (amended compilation)](https://www.indiacode.nic.in/bitstream/123456789/2046/4/a2003-18.pdf) — unavailable. Includes 2023 amendments; applicability and commencement require review.
- [Biological Diversity ABS Regulations, 2025](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_16_18_000010_200318_1517807327125&filename=abs_regulations_2025_%285%29-1.pdf&type=regulation) — unavailable. Official regulation text, distinct from the dynamic CBD national record.
- [Food Safety and Standards (Ayurveda Aahara) Regulations, 2022](https://www.fssai.gov.in/upload/notifications/2022/05/62789a20b54bdGazette_Notification_Ayurveda_Aahara_09_05_2022.pdf) — acquired but no usable extracted passages. Base Gazette; subsequent orders are separate source versions.
- Supplied [original link](https://fssai.gov.in/docs/food-law/advisory/68b685259cb03Order%20dated01stSeptember2025-Introduction%20of%20new%20KoB-Ayurveda%20aahara.pdf) replaced by `aahara-kob`: Original URL failed during planning; official alternate discovered.

### Implementation references

- [Gemini API terms](https://ai.google.dev/gemini-api/terms) and [pricing](https://ai.google.dev/gemini-api/docs/pricing) — provider/privacy planning; inspected 2026-09-06; deployment must recheck terms and quotas.
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) — risk-control mapping; inspected 2026-09-06; no certification claimed.
- [OWASP LLM application risks](https://genai.owasp.org/llm-top-10/) — threat-model reference; inspected 2026-09-06.
- [Multilingual E5-small model](https://huggingface.co/intfloat/multilingual-e5-small) — local embeddings; immutable revision in `corpus/model-lock.json`, resolved 2026-09-06.
- [Bhashini](https://bhashini.gov.in/) — language-service integration target; credential-tested state is false.
<!-- BIBLIOGRAPHY:END -->
