from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import SourceVersion
from app.providers import plan_queries
from app.retrieval import retrieve_queries


def test_planner_bounds_untrusted_model_output(monkeypatch):
    monkeypatch.setattr('app.providers.generate',lambda *_:{'queries':['patent novelty',7,'x','a'*1001,'ignored']})
    assert plan_queries('original question','india','treaties')==['original question','patent novelty']


def test_multiquery_fusion_preserves_scope(library):
    with SessionLocal() as db:
        rows,metrics=retrieve_queries(db,['traditional knowledge patent','botanical drug regulatory route'],'india')
        assert rows and metrics['query_count']==2
        assert all(s.jurisdiction=='india' for _,_,s in rows)
        assert len({c.id for c,_,_ in rows})==len(rows)


def test_reference_rag_generates_but_never_claims_review(client,library,monkeypatch):
    monkeypatch.setattr(settings(),'generation_provider','gemini')
    monkeypatch.setattr(settings(),'reference_synthesis_enabled',True)
    with SessionLocal() as db:
        for v in db.scalars(select(SourceVersion)):
            v.review_status='reference_only'
        db.commit()
    calls=[]
    def model(system,payload):
        calls.append(payload)
        if 'queries' in system:
            return {'queries':['traditional knowledge patent formulation']}
        if system.startswith('You check evidence'):
            return {'supported':[0]}
        e=payload['evidence'][0]
        assert e['review_status']=='reference_only'
        return {'claims':[{'text':'The supplied document describes prior-art assessment of a traditional formulation.',
                          'citation_ids':[e['id']],'support_quote':e['text']}]}
    monkeypatch.setattr('app.providers.generate',model)
    r=client.post('/api/v1/questions',json={'query':'Does that apply to my formulation?',
        'previous_questions':['Can traditional knowledge be patented?'],'cloud_consent':True}).json()
    assert r['mode']=='generated' and r['evidence_status']=='partial'
    assert r['metrics']['llm_query_planning'] is True
    assert len(calls)==3
    assert calls[0]['previous_questions']==['Can traditional knowledge be patented?']
    assert any('not verified current-law' in s for s in r['limitations'])


def test_private_history_never_reaches_cloud_planner(client,library,monkeypatch):
    monkeypatch.setattr(settings(),'generation_provider','gemini')
    def forbidden(*args):raise AssertionError('Private context reached cloud')
    monkeypatch.setattr('app.providers.generate',forbidden)
    response=client.post('/api/v1/questions',json={'query':'traditional knowledge patent',
        'previous_questions':['My confidential unpublished formulation'],'cloud_consent':True})
    assert response.status_code==200 and response.json()['mode']=='retrieval'

