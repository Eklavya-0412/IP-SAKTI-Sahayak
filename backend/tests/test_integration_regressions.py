import pytest
from app.config import Settings
from app.db import SessionLocal
from app.main import app
from fastapi.testclient import TestClient

@pytest.mark.parametrize('origin',[f'http://{host}:{port}' for host in ('localhost','127.0.0.1') for port in (5173,8080)])
def test_local_origin_post_and_preflight(client,origin):
 r=client.options('/api/v1/questions',headers={'Origin':origin,'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'Content-Type,X-CSRF-Token'})
 assert r.status_code==200
 assert r.headers['access-control-allow-origin']==origin
 r=client.post('/api/v1/questions',headers={'Origin':origin},json={'query':'patent traditional knowledge'})
 assert r.status_code==200
 assert r.headers['access-control-allow-origin']==origin


def test_production_excludes_localhost():
 cfg=Settings(_env_file=None,app_env='production',public_origin='https://legal.example')
 assert cfg.trusted_origins==['https://legal.example']


def test_trusted_origin_still_requires_csrf(client):
 client.headers.pop('X-CSRF-Token')
 assert client.post('/api/v1/questions',headers={'Origin':'http://localhost:5173'},json={'query':'patent knowledge'}).status_code==403


def test_stream_returns_stage_and_answer(client,library):
 r=client.post('/api/v1/questions/stream',json={'query':'traditional knowledge patent formulation'})
 assert r.status_code==200
 assert 'event: stage' in r.text
 assert 'event: answer' in r.text
 assert 'event: error' not in r.text


def test_retry_never_broadens_market(monkeypatch):
 from app.assistant import retrieve_agent
 from app.schemas import Question
 calls=[]
 def retrieve(db,queries,jurisdiction,market,as_of):
  calls.append((jurisdiction,market));return [],{}
 monkeypatch.setattr('app.assistant.retrieve_queries',retrieve)
 monkeypatch.setattr('app.assistant.expand_graph',lambda *args:([],[]))
 with SessionLocal() as db:
  retrieve_agent({'question':Question(query='botanical drug approval',jurisdiction='international',market='us'), 'db':db,'retry_count':1,'rows':[]})
 assert calls==[('international','us')]


def test_bootstrap_in_another_tab_does_not_invalidate_token(client):
 first=client.get('/api/v1/auth/session').json()['csrf_token']
 second=client.get('/api/v1/auth/session').json()['csrf_token']
 assert first==second
 response=client.post('/api/v1/questions',headers={'X-CSRF-Token':first},json={'query':'traditional knowledge patents'})
 assert response.status_code==200


def test_local_query_plan_keeps_international_queries_unchanged():
 from app.retrieval import local_query_plan
 query='Can a botanical formulation be patented?'
 assert local_query_plan([query],'international')==[query]
 assert len(local_query_plan([query],'india'))==3
