import pytest
from app.assessments import classify,assess_abs
from app.db import SessionLocal
from conftest import sign_in

@pytest.mark.parametrize('facts,expected',[
 ({'use':'therapeutic','reference':'yes','exact':'yes'},'classical'),
 ({'use':'therapeutic','reference':'yes','exact':'no','ingredients':'yes'},'proprietary'),
 ({'use':'therapeutic','reference':'no','ingredients':'no','phytopharma':'yes'},'phytopharmaceutical'),
 ({'use':'therapeutic','reference':'no','ingredients':'no','phytopharma':'no'},'new_drug'),
 ({'use':'nutrition','aahara':'yes'},'aahara'),({'use':'nutrition','aahara':'no'},'food'),
 ({'use':'cosmetic'},'cosmetic'),({'use':'unknown'},'uncertain'),
 ({'use':'therapeutic','reference':'unknown'},'uncertain')])
def test_classification_routes(facts,expected):
    with SessionLocal() as db:
        r=classify(db,{**facts,'route':'oral','origin':'plant'})
        assert r['complete'] and r['code']==expected and r['provisional']

def test_minimal_clarification():
    with SessionLocal() as db:
        assert classify(db,{'use':'cosmetic'})['question']['id']=='route'
        assert classify(db,{'use':'nutrition'})['question']['id']=='aahara'
        assert classify(db,{'use':'unknown'})['complete']

def test_unknown_answers_not_forced():
    with SessionLocal() as db:
        r=classify(db,{'use':'therapeutic','reference':'no','ingredients':'unknown','route':'oral','origin':'mixed'})
        assert r['complete'] and r['code']=='uncertain'

def test_invalid_assessment_answers(client):
    assert client.post('/api/v1/assessments/classification',json={'answers':{'use':'make_up_a_drug'}}).status_code==422

def test_assessment_session_ownership(client):
    id=client.post('/api/v1/assessments/abs',json={}).json()['assessment_id']
    client.post('/api/v1/auth/logout')
    client.headers['X-CSRF-Token']=client.get('/api/v1/auth/session').json()['csrf_token']
    assert client.post('/api/v1/assessments/abs',json={'assessment_id':id}).status_code==404

def test_abs_no_blanket_cultivation_exemption():
    with SessionLocal() as db:
        r=assess_abs(db,{'origin':'yes','entity':'indian','purpose':'commercial','transfer':'no','ip':'no','cultivated':'yes','tk':'yes'})
        assert r['code']=='sbb' and any('alone' in s for s in r['limitations'])

def test_facilitator_state_transitions(client):
    sign_in(client,role='facilitator')
    case=client.post('/api/v1/cases',json={'title':'Facilitator test','content':{'history':[{'question':'private detail'}]}}).json()
    review=client.post('/api/v1/cases/'+case['id']+'/review',json={'summary':'Share this summary only','include_history':False}).json()
    listing=client.get('/api/v1/reviews').json()
    assert 'history' not in listing[0]['shared_content']
    url='/api/v1/reviews/'+review['id']
    assert client.patch(url,json={'status':'resolved','response':'Premature resolution'}).status_code==409
    assert client.patch(url,json={'status':'assigned'}).status_code==200
    assert client.patch(url,json={'status':'in_review'}).status_code==200
    assert client.patch(url,json={'status':'resolved','response':'Please consult the responsible licensing authority.'}).status_code==200

def test_missing_language_credentials(client):
    assert client.post('/api/v1/language',json={'task':'translation','source':'en','target':'hi','text':'Public patent guidance','allow_cloud':True}).status_code==503

def test_job_failure_does_not_activate_sources(client):
    sign_in(client,role='curator')
    assert client.post('/api/v1/admin/jobs',json={'kind':'ingest','source_id':'made-up'}).status_code==404
