import io
from sqlalchemy import select
from app.db import SessionLocal
from app.models import PrivateDocument,Consent,AuditEvent,User
from app.providers import privacy_gate,PrivacyBlocked
from app.config import settings
from conftest import sign_in
import pytest

def test_csrf_required(client):
    client.headers.pop('X-CSRF-Token')
    r=client.post('/api/v1/questions',json={'query':'patent traditional knowledge'})
    assert r.status_code==403

def test_cross_origin_blocked(client):
    assert client.post('/api/v1/questions',headers={'Origin':'https://evil.example'},json={'query':'patent knowledge'}).status_code==403

def test_session_rotation(client):
    old=client.cookies.get('ipsakti_session');sign_in(client)
    assert client.cookies.get('ipsakti_session')!=old

def test_wrong_password(client):
    sign_in(client)
    assert client.post('/api/v1/auth/login',json={'email':'user@example.com','password':'incorrect-passphrase'}).status_code==401

def test_roles_are_server_enforced(client):
    sign_in(client)
    assert client.get('/api/v1/admin/audit').status_code==403
    assert client.post('/api/v1/admin/jobs',json={'kind':'purge'}).status_code==403

def test_guest_cannot_save(client):
    assert client.post('/api/v1/cases',json={'title':'Private case'}).status_code==401

def test_case_ownership_and_deletion(client):
    sign_in(client)
    case=client.post('/api/v1/cases',json={'title':'Owner private case'}).json()
    client.post('/api/v1/auth/logout')
    client.headers['X-CSRF-Token']=client.get('/api/v1/auth/session').json()['csrf_token']
    sign_in(client,'other@example.com')
    assert client.delete('/api/v1/cases/'+case['id']).status_code==404
    assert client.get('/api/v1/cases/'+case['id']+'/export').status_code==404
    assert client.get('/api/v1/cases/'+case['id']+'/documents').status_code==404

def test_private_documents_never_enter_sources(client,library):
    sign_in(client);case=client.post('/api/v1/cases',json={'title':'Secret'}).json()
    url='/api/v1/cases/'+case['id']+'/documents'
    assert client.post(url,data={'permission':'false'},files={'file':('secret.txt',b'Secret patent ratio 8372 X', 'text/plain')}).status_code==422
    result=client.post(url,data={'permission':'true'},files={'file':('secret.txt',b'Secret patent ratio 8372 X','text/plain')})
    assert result.status_code==201
    answer=client.post('/api/v1/questions',json={'query':'patent ratio 8372 X'}).json()
    assert '8372' not in str(answer['citations'])
    client.delete('/api/v1/cases/'+case['id'])
    with SessionLocal() as db:assert not db.scalar(select(PrivateDocument))

def test_fake_pdf_rejected(client):
    sign_in(client);case=client.post('/api/v1/cases',json={'title':'Test'}).json()
    assert client.post('/api/v1/cases/'+case['id']+'/documents',data={'permission':'true'},files={'file':('fake.pdf',b'<script>bad</script>','application/pdf')}).status_code==415

def test_consent_is_scoped_and_revocable(client):
    sign_in(client)
    body={'provider':'test-vendor','scope':'search','query':'patent search'}
    assert client.post('/api/v1/connectors/access',json=body).status_code==403
    consent=client.post('/api/v1/consents',json={'provider':'test-vendor','scope':'search','purpose':'Search my licensed database'}).json()
    assert client.post('/api/v1/connectors/access',json=body).status_code==503
    assert client.post('/api/v1/connectors/access',json={**body,'scope':'read'}).status_code==403
    assert client.delete('/api/v1/consents/'+consent['id']).status_code==200
    assert client.post('/api/v1/connectors/access',json=body).status_code==403
    with SessionLocal() as db:assert db.scalar(select(AuditEvent).where(AuditEvent.action=='consent.revoked'))

@pytest.mark.parametrize('query,private,consent',[
    ('my confidential invention',False,True),('email me at person@example.com',False,True),
    ('patent requirements',True,True),('patent requirements',False,False),('मेरा गोपनीय सूत्र',False,True)])
def test_free_cloud_privacy(query,private,consent,monkeypatch):
    monkeypatch.setattr(settings(),'generation_provider','gemini')
    with pytest.raises(PrivacyBlocked):privacy_gate(query,private,consent)

def test_cloud_general_question_allowed(monkeypatch):
    monkeypatch.setattr(settings(),'generation_provider','gemini')
    privacy_gate('What is a patent?',False,True)

def test_account_deletion_invalidates_session(client):
    user_id=sign_in(client)
    client.post('/api/v1/cases',json={'title':'Delete me'})
    assert client.delete('/api/v1/account').status_code==200
    assert client.get('/api/v1/cases').status_code==401
    with SessionLocal() as db:assert db.get(User,user_id) is None

def test_no_audio_without_valid_wav(client):
    assert client.post('/api/v1/language',json={'task':'asr','audio':'aW52YWxpZA==','allow_cloud':True}).status_code==422
