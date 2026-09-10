"""Actual corpus evaluation. Scores mechanics separately from human legal correctness."""
import argparse,json,sys,time,platform,statistics
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.db import SessionLocal
from app.assistant import answer_question
from app.schemas import Question
from app.models import Chunk,Source,EvaluationRun
from app.corpus import active_release

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int);parser.add_argument('--output',default='evals/results/latest.json');args=parser.parse_args()
    scenarios=[json.loads(l) for l in (ROOT/'evals/scenarios.jsonl').read_text(encoding='utf-8').splitlines()]
    if args.limit:scenarios=scenarios[:args.limit]
    results=[];started=time.time()
    with SessionLocal() as db:
        release=active_release(db)
        for n,s in enumerate(scenarios):
            for language,query in s['queries'].items():
                tick=time.perf_counter()
                answer=answer_question(db,Question(query=query,language=language,jurisdiction=s['jurisdiction'],market=s['market']))
                lookup={c.id:c for c in answer.citations}
                results.append({'scenario':s['id'],'language':language,'category':s['category'],'mode':answer.mode,
                    'retrieval':answer.metrics.get('retrieval'),'embedding_error':answer.metrics.get('embedding_error'),
                    'elapsed_ms':round((time.perf_counter()-tick)*1000,2),'trace_id':answer.trace_id,'citation_ids':list(lookup),
                    'citation_resolution':all(db.get(Chunk,c.id) is not None for c in answer.citations),
                    'jurisdiction_isolation':all(c.jurisdiction==s['jurisdiction'] and c.market==s['market'] for c in answer.citations),
                    'literal_integrity':all(cl.support_quote in lookup[cl.citation_ids[0]].excerpt for cl in answer.claims),
                    'abstention_expected':s['expected']=='abstention','abstention_correct':answer.mode=='abstention' if s['expected']=='abstention' else None,
                    'topic_recall':any(db.get(Source,c.source_id).category==s['category'] for c in answer.citations),
                    'legal_correctness':None,'citation_entailment_review':None,'translation_quality':None})
            print(f'{n+1}/{len(scenarios)} {s["id"]}',flush=True)
        summary={}
        for language in ['en','hi','mr']:
            items=[r for r in results if r['language']==language];times=sorted(r['elapsed_ms'] for r in items);adv=[r for r in items if r['abstention_expected']]
            summary[language]={'n':len(items),'modes':dict(Counter(r['mode'] for r in items)),
                'citation_resolution':sum(r['citation_resolution'] for r in items)/len(items),
                'jurisdiction_isolation':sum(r['jurisdiction_isolation'] for r in items)/len(items),
                'literal_integrity':sum(r['literal_integrity'] for r in items)/len(items),
                'adversarial_n':len(adv),'safe_abstention':sum(r['abstention_correct'] for r in adv)/len(adv) if adv else None,
                'p50_ms':statistics.median(times),'p95_ms':times[min(len(times)-1,int(.95*len(times)))],
                'legal_accuracy':None,'citation_support_accuracy':None,'language_quality':None}
        report={'generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'corpus_release':release.id if release else None,
            'hardware':{'platform':platform.platform(),'processor':platform.processor(),'python':platform.python_version()},
            'execution':'Sequential actual-corpus calls; source-only mode. No paid tokens or model-generated answers.',
            'duration_seconds':round(time.time()-started,2),'summary':summary,'results':results,
            'limitations':['Mechanics scores include vacuous passes for abstentions; inspect response-mode counts.','Exact excerpt containment is not legal entailment or relevance.','Legal correctness and all human language-review gates are unmeasured.','A templated scenario family is broader coverage, not independent expert validation.']}
        target=ROOT/args.output;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        db.add(EvaluationRun(dataset_version='2026.09.1',report=report));db.commit()
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
