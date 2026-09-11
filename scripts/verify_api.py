"""Validate live HTTP status, answer schema, nonempty evidence and scope.
Run after corpus ingestion and starting Uvicorn. No credentials are printed.
"""
import argparse,json,sys
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.schemas import Answer


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--base',default='http://127.0.0.1:8000/api/v1')
 p.add_argument('--cloud',action='store_true',help='Consent to Groq for these general, nonconfidential questions')
 p.add_argument('--report',type=Path,default=ROOT/'docs/phase3-live-http.json')
 args=p.parse_args();results=[]
 with httpx.Client(base_url=args.base,timeout=180) as client:
  session=client.get('/auth/session');session.raise_for_status()
  csrf=session.json()['csrf_token']
  for jurisdiction,market,query in [('india','treaties','Is neem paste patentable under Section 3(p) of the Patents Act?'),('india','treaties','Can I patent an Ayurvedic formulation of ginger and turmeric?'),('international','us','What are the regulatory requirements for botanical drug approval?')]:
   body={'query':query,'jurisdiction':jurisdiction,'market':market,'language':'en','previous_questions':[],'cloud_consent':args.cloud}
   response=client.post('/questions',json=body,headers={'Origin':'http://127.0.0.1:5173','X-CSRF-Token':csrf})
   result={'query':query,'status':response.status_code,'pass':False}
   if response.status_code==200:
    answer=Answer.model_validate(response.json());result['answer']=answer.model_dump()
    ids={c.id for c in answer.citations}
    result['pass']=bool(answer.claims and answer.citations) and all(c.jurisdiction==jurisdiction and c.market==market for c in answer.citations) and all(set(c.citation_ids)<=ids for c in answer.claims)
   results.append(result)
 args.report.parent.mkdir(parents=True,exist_ok=True)
 args.report.write_text(json.dumps({'results':results,'pass':all(r['pass'] for r in results)},indent=2),encoding='utf-8')
 print(json.dumps([{k:v for k,v in r.items() if k!='answer'} for r in results],indent=2))
 raise SystemExit(0 if all(r['pass'] for r in results) else 1)

if __name__=='__main__':main()
