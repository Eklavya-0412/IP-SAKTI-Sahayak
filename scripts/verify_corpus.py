"""Read-only corpus verification and strict live retrieval benchmarks.
Exit nonzero on empty vectors, missing sources, or scope leakage.
"""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark',action='store_true')
    parser.add_argument('--report',type=Path,default=ROOT/'docs/corpus-verification.json')
    args=parser.parse_args()
    from sqlalchemy import text,select
    from app.db import SessionLocal
    from app.models import CorpusRelease,SourceVersion
    from app.retrieval import retrieve_queries,expand_graph
    report={'checks':{},'benchmarks':[]}
    with SessionLocal() as db:
        vector_count=db.scalar(text('SELECT count(*) FROM chunks WHERE vector_embedding IS NOT NULL'))
        total=db.scalar(text('SELECT count(*) FROM chunks'))
        releases=db.scalars(select(CorpusRelease).where(CorpusRelease.active==True)).all()
        active_ids=releases[0].version_ids if len(releases)==1 else []
        active_vectors=db.scalar(text('SELECT count(*) FROM chunks WHERE version_id=ANY(:ids) AND vector_embedding IS NOT NULL'),{'ids':active_ids}) if active_ids else 0
        report['counts']={'chunks':total,'non_null_vectors':vector_count,'active_releases':len(releases),'active_vectors':active_vectors}
        report['checks']={'nonempty_vectors':vector_count>0,'one_active_release':len(releases)==1,'active_release_has_vectors':active_vectors>0}
        if args.benchmark:
            cases=[('india','treaties','Can I patent an Ayurvedic formulation of ginger and turmeric?',
                    {'patents-act','ayush-guidelines','biodiversity-act'}),
                   ('international','us','What are the regulatory requirements for botanical drug approval?',{'us-botanical'})]
            for jurisdiction,market,query,expected in cases:
                rows,metrics=retrieve_queries(db,[query],jurisdiction,market)
                rows,_=expand_graph(db,rows,jurisdiction,market)
                found={s.id for _,_,s in rows}
                scope_ok=all(s.jurisdiction==jurisdiction and s.market==market for _,_,s in rows)
                missing=sorted(expected-found)
                report['benchmarks'].append({'jurisdiction':jurisdiction,'market':market,'query':query,
                    'source_ids':sorted(found),'missing_expected_sources':missing,'scope_isolated':scope_ok,
                    'pass':bool(rows) and scope_ok and not missing,'metrics':metrics,
                    'evidence':[{'source_id':s.id,'locator':c.locator,'excerpt':c.text} for c,_,s in rows]})
    report['pass']=all(report['checks'].values()) and all(b['pass'] for b in report['benchmarks'])
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'counts':report['counts'],'checks':report['checks'],'pass':report['pass']}))
    raise SystemExit(0 if report['pass'] else 1)

if __name__=='__main__':main()
