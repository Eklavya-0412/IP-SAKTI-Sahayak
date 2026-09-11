from pathlib import Path
import json,os,sys
root=Path(__file__).resolve().parents[1];os.environ['DATABASE_URL']='sqlite://';os.environ['EMBEDDINGS_ENABLED']='false';os.environ['GENERATION_PROVIDER']='none';sys.path.insert(0,str(root/'backend'))
from app.db import Base,engine,SessionLocal
from app.models import Source,SourceVersion,Chunk,CorpusRelease
from app.retrieval import retrieve_queries,expand_graph
Base.metadata.create_all(engine)
manifest=json.loads((root/'corpus/manifest.json').read_text())['sources'];entries={e['id']:e for e in manifest};ids=[]
with SessionLocal() as db:
 for report in ['docs/ingestion-report.json','docs/benchmark-ingestion-report.json']:
  for d in json.loads((root/report).read_text())['documents']:
   e=entries[d['source_id']];db.add(Source(**{k:e[k] for k in ['id','title','publisher','url','jurisdiction','market','authority','category']}));db.flush()
   v=SourceVersion(source_id=e['id'],checksum=d['sha256'],path=d['file'],review_status='reference_only');db.add(v);db.flush();ids.append(v.id)
   cached=json.loads((root/'data/extractions'/(d['sha256']+'-chunks-v1.json')).read_text(encoding='utf-8'))
   db.add_all([Chunk(version_id=v.id,**c) for c in cached['chunks']])
 db.add(CorpusRelease(name='Offline extracted documents',version_ids=ids,active=True));db.commit()
 results=[]
 for j,m,q,expect in [('india','treaties','Can I patent an Ayurvedic formulation of ginger and turmeric?',{'patents-act','ayush-guidelines','biodiversity-act'}),('international','us','What are the regulatory requirements for botanical drug approval?',{'us-botanical'})]:
  rows,metrics=retrieve_queries(db,[q],j,m);rows,_=expand_graph(db,rows,j,m);found={s.id for _,_,s in rows}
  results.append({'jurisdiction':j,'market':m,'source_ids':sorted(found),'missing_expected_sources':sorted(expect-found),'scope_isolated':all(s.jurisdiction==j and s.market==m for _,_,s in rows),'metrics':metrics,'evidence':[{'source_id':s.id,'locator':c.locator,'excerpt':c.text} for c,v,s in rows]})
 print(json.dumps([{k:v for k,v in result.items() if k!='evidence'} for result in results],indent=2))
 assert all(result['scope_isolated'] and not result['missing_expected_sources'] for result in results)
 (root/'docs/offline-benchmark.json').write_text(json.dumps({'mode':'offline SQLite, lexical retrieval, actual extracted PDFs','results':results},indent=2))
