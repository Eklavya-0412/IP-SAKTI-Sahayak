"""Generate truthful submission metadata from the live corpus and actual test outputs."""
import json,re,sys,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.db import SessionLocal
from app.models import Source,SourceVersion,Chunk
from app.corpus import active_release
from sqlalchemy import select,func

def write(path,text):
    target=ROOT/path;target.parent.mkdir(exist_ok=True,parents=True);target.write_text(text,encoding='utf-8')

manifest=json.loads((ROOT/'corpus/manifest.json').read_text(encoding='utf-8'))
inventory=[];coverage=defaultdict(lambda:{'registered':0,'acquired':0,'searchable':0,'approved':0})
with SessionLocal() as db:
    release=active_release(db)
    for entry in manifest['sources']:
        versions=db.scalars(select(SourceVersion).where(SourceVersion.source_id==entry['id']).order_by(SourceVersion.retrieved_at.desc())).all()
        item={**entry,'versions':[]}
        for v in versions:
            count=db.scalar(select(func.count()).select_from(Chunk).where(Chunk.version_id==v.id))
            item['versions'].append({'id':v.id,'sha256':v.checksum,'retrieved_at':v.retrieved_at.isoformat(),'effective_from':v.effective_from,
              'effective_to':v.effective_to,'publication_date':v.publication_date,'review_status':v.review_status,'review_note':v.review_note,
              'chunks':count,'quality':v.quality,'active':bool(release and v.id in release.version_ids)})
        if entry.get('local_path'):
            item['original_sha256']=hashlib.sha256((ROOT/entry['local_path']).read_bytes()).hexdigest()
        inventory.append(item)
        key=f"{entry['jurisdiction']} / {entry['market']} / {entry['category']}";row=coverage[key];row['registered']+=1;row['acquired']+=bool(versions)
        row['searchable']+=any(v['active'] and v['chunks'] for v in item['versions']);row['approved']+=any(v['review_status']=='approved' for v in item['versions'])
write('corpus/inventory.json',json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),'sources':inventory},ensure_ascii=False,indent=2))
lines=['# Coverage matrix','','Counts reflect actual acquisition and release membership, not legal completeness. Zero approved sources means generated legal guidance remains gated.','','| Scope / category | Registered | Acquired | Searchable | Approved |','|---|---:|---:|---:|---:|']
for k,v in sorted(coverage.items()):lines.append(f"| {k} | {v['registered']} | {v['acquired']} | {v['searchable']} | {v['approved']} |")
lines+=['','## Remaining authority gaps','','Current consolidated drug/advertising/cosmetics requirements; current judgments; lawfully accessible pharmacopoeial monographs; authoritative-text verification; state-specific procedures; treaty membership and entry-into-force records; EU member-state pathways; amendment review of all supplied compilations. Inaccessible or empty publisher responses remain unusable until reacquired.']
write('corpus/coverage.md','\n'.join(lines)+'\n')
bib=['### Acquired sources','','Acquisition dates and hashes are in `corpus/inventory.json`. “Reference only” does not mean approved current law.']
unused=['### Disposition register','','These supplied/registered resources are excluded, unavailable, background, or access pointers. They cannot support legal conclusions merely because they are listed.']
for s in inventory:
    useful=[v for v in s['versions'] if v['chunks']]
    used=bool(useful) and s.get('disposition') not in ('excluded','pointer','background')
    if used:
        v=useful[0];local=f" Supplied file: `{s['local_path']}`." if s.get('local_path') else ''
        bib.append(f"- [{s['title']}]({s['url']}) — {s['publisher']}; {s['authority']}; purpose: {s['category'].replace('_',' ')}; accessed {v['retrieved_at'][:10]}; {v['review_status']}, {v['chunks']} chunks.{local} {s.get('notes','')}")
    else:
        state=s.get('disposition','unavailable') if not s['versions'] else 'acquired but no usable extracted passages'
        unused.append(f"- [{s['title']}]({s['url']}) — {state}. {s.get('notes','')}" )
for replacement in manifest.get('supplied_url_replacements',[]):unused.append(f"- Supplied [original link]({replacement['original']}) replaced by `{replacement['replacement_id']}`: {replacement['reason']}")
bib+=['']+unused+['','### Implementation references','',
 '- [Gemini API terms](https://ai.google.dev/gemini-api/terms) and [pricing](https://ai.google.dev/gemini-api/docs/pricing) — provider/privacy planning; inspected 2026-09-06; deployment must recheck terms and quotas.',
 '- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) — risk-control mapping; inspected 2026-09-06; no certification claimed.',
 '- [OWASP LLM application risks](https://genai.owasp.org/llm-top-10/) — threat-model reference; inspected 2026-09-06.',
 '- [Multilingual E5-small model](https://huggingface.co/intfloat/multilingual-e5-small) — local embeddings; immutable revision in `corpus/model-lock.json`, resolved 2026-09-06.',
 '- [Bhashini](https://bhashini.gov.in/) — language-service integration target; credential-tested state is false.']
readme=(ROOT/'README.md').read_text(encoding='utf-8');readme=re.sub(r'<!-- BIBLIOGRAPHY:START -->.*?<!-- BIBLIOGRAPHY:END -->','<!-- BIBLIOGRAPHY:START -->\n'+'\n'.join(bib)+'\n<!-- BIBLIOGRAPHY:END -->',readme,flags=re.S);write('README.md',readme)

evaluation_path=ROOT/'evals/results/latest.json';evaluation=json.loads(evaluation_path.read_text()) if evaluation_path.exists() else {}
deployment_path=ROOT/'docs/deployment-results.json';deployment=json.loads(deployment_path.read_text()) if deployment_path.exists() else {'status':'not yet run'}
tests_path=ROOT/'docs/test-results.xml';tests={}
if tests_path.exists():
    suite=ET.parse(tests_path).getroot().find('testsuite');tests=suite.attrib if suite is not None else {}
report=['# Evaluation report','','Generated from actual executions; no simulated results.','',f"Corpus release tested: `{evaluation.get('corpus_release','not measured')}`.",
 f"Automated backend tests: {tests.get('tests','unknown')}; failures: {tests.get('failures','unknown')}; errors: {tests.get('errors','unknown')}.",
 f"Docker/restore rehearsal: **{deployment['status']}**. Details: `docs/deployment-results.json`.",'',
 '| Language | Executions | Retrieval / abstention | Citation resolution | Scope isolation | p50 / p95 ms |','|---|---:|---|---:|---:|---:|']
for lang,row in evaluation.get('summary',{}).items():
    report.append(f"| {lang} | {row['n']} | {row['modes'].get('retrieval',0)} / {row['modes'].get('abstention',0)} | {row['citation_resolution']:.0%} | {row['jurisdiction_isolation']:.0%} | {row['p50_ms']:.0f} / {row['p95_ms']:.0f} |")
report+=['','## What these results establish','','Returned chunk IDs resolve, original excerpts retain literal integrity, and returned citations stay within the selected jurisdiction/market. An abstention has no citations and therefore vacuously passes these mechanical checks; response counts must be considered. The adversarial set has only four scenarios per language, so 100% on that small set does not establish general safe-abstention accuracy.','',
 '## Unmeasured gates','','Qualified substantive correctness, genuine citation relevance/entailment, complete safe-abstention accuracy, legal translation quality, and live voice quality remain **unmeasured**. The proposed 95% citation-support and 90% legal-correctness gates are not claimed met. Zero expert-reviewed scenarios are currently recorded. Source-only execution consumes no generation API tokens; hosted latency, quota and cost are not inferred from local timings.','',
 '## Reproduction','','Run `python scripts/build_evaluation.py` then `python scripts/evaluate.py` using the same snapshot release. This dataset contains 123 substantive scenarios (41 topics × 3 evidence tasks), each in English/Hindi/Marathi, plus four adversarial scenarios in each language: 381 executions. Questions are templated families and need independent expert expansion. The runner saves per-execution trace IDs, citation IDs, modes, timings and null human scores.','',
 '## Hardware and conditions','', '```json',json.dumps(evaluation.get('hardware',{}),indent=2),'```','',evaluation.get('execution','Not executed.'),
 '', 'The evaluator is sequential; HTTP concurrency, semantic-model latency and remote-provider performance require separate measurements. Run the deployment rehearsal for PostgreSQL/HTTP verification. Raw results: `evals/results/latest.json`; tests: `docs/test-results.xml`.']
hybrid_path=ROOT/'evals/results/hybrid-sample.json'
if hybrid_path.exists():
    hybrid=json.loads(hybrid_path.read_text())
    report+=['','## Local semantic-retrieval sample','','A separate 36-execution sample used the pinned, downloaded E5 model. Trace records show '+str(hybrid.get('retrieval_modes',{}))+'. These are actual retrieval modes; pre-retrieval abstentions have no retrieval mode. Source coverage and relevance still require expert review.','', '| Language | Sample n | p50 / p95 ms |','|---|---:|---:|']
    for language,row in hybrid['summary'].items():report.append(f"| {language} | {row['n']} | {row['p50_ms']:.0f} / {row['p95_ms']:.0f} |")
write('docs/EVALUATION.md','\n'.join(report)+'\n')

summary={'sources_registered':len(inventory),'source_versions':sum(len(s['versions']) for s in inventory),'active_chunks':sum(v['chunks'] for s in inventory for v in s['versions'] if v['active']),
 'approved_versions':sum(v['review_status']=='approved' for s in inventory for v in s['versions']),'original_pdfs':sum(bool(s.get('local_path')) for s in inventory),
 'backend_tests':tests,'deployment':deployment,'evaluation':evaluation.get('summary',{}),'corpus_release':release.id if release else None}
write('docs/submission-metrics.json',json.dumps(summary,indent=2))
project=['# IP-SAKTI Sahayak','## Complete Deployable Pilot — Project Report','',
 'Prepared 6 September 2026. Information, not legal advice. This report describes implemented software, observed evidence and outstanding external release gates.','',
 '## Purpose and beneficiaries','',
 'Ayurveda innovation crosses intellectual property, biological-resource access and product regulation. The pilot helps practitioners, researchers, startups, MSMEs and cultivators navigate those questions with inspectable sources. It separates jurisdictions and product categories instead of treating every herbal formulation as the same legal object.','',
 '## Delivered system','',
 f"The workspace contains {summary['sources_registered']} registered source candidates, {summary['source_versions']} acquired versions and {summary['active_chunks']} chunks in the active reference release. The {summary['original_pdfs']} supplied PDFs are preserved and checksummed. {summary['approved_versions']} versions are approved for generated current-law guidance. These counts distinguish acquisition from expert applicability review.",
 '', 'The application includes a multilingual assistant workspace, source viewer, formulation/ABS assessments, case ownership and imports, selected facilitator submissions, consent controls, administration, background acquisition/retention, bounded orchestration and graph evidence. It works in source-search mode without paid keys. External language and generation adapters have honest configuration states.','',
 '## Design decisions','',
 'Local embeddings avoid mandatory embedding subscriptions. PostgreSQL stores retrieval, graph and operational records together. Immutable source snapshots enable provenance inspection. Source review and answer generation are separate gates. Private facts are confined to local inference. Original legal excerpts remain available when translations cannot be verified.','',
 '## Acceptance and limitations','',
 'Mechanical tests and actual corpus execution provide evidence of behavior, not proof of legal accuracy. Qualified review, live provider validation, corpus completeness, production security hardening and deployment-specific DPDP applicability remain required. No public launch, facilitator staffing or paid source access has been provisioned.','']
for filename in ['ARCHITECTURE.md','FEATURE_STATUS.md','EVALUATION.md','SECURITY.md','OPERATIONS.md','USER_GUIDE.md','REVIEW_GUIDE.md','DEMO_SCRIPT.md']:
    project+=['\n---\n',(ROOT/'docs'/filename).read_text(encoding='utf-8')]
project+=['\n---\n','## Source traceability and reproducibility','',
 'The complete resource bibliography is generated in README.md. corpus/inventory.json retains source version identifiers, byte checksums, retrieval dates, extraction diagnostics and release membership. corpus/coverage.md identifies searchable/approved scope and known gaps. Source snapshots remain under data/snapshots or the Docker document volume; reacquisition commands are in the runbook. Do not redistribute proprietary pharmacopoeial or restricted registry content without permission.','',
 '## Next release gates','',
 'Complete qualified source and classification review; acquire missing legal instruments and permitted standards; score answer responsiveness and legal correctness; validate all three languages and live voice; test hosted/local generation against the reviewed corpus; complete production authentication/abuse/privacy review; assign a facilitator team; rehearse encrypted backup rotation and incident response on the intended host.']
write('docs/PROJECT_REPORT.md','\n'.join(project)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['evaluation','backend_tests','deployment']},indent=2))
