from app.config import settings
from app.db import SessionLocal
from app.retrieval import retrieve,citation
from app.providers import draft_and_verify

def test_valid_evidence_id_resolves_without_model_transcription(library,monkeypatch):
    with SessionLocal() as db: sources=[citation(r) for r in retrieve(db,'traditional knowledge patent','india')[0]]
    source=sources[0]
    replies=iter([{'claims':[{'text':'Prior art must be considered.','citation_ids':[source.id],'support_id':source.id}]},{'supported':[0]}])
    monkeypatch.setattr('app.providers.generate',lambda *_:next(replies))
    metrics={}
    claims=draft_and_verify('patent',sources,'india','treaties',diagnostics=metrics)
    assert claims[0]['support_quote']==source.excerpt
    assert metrics=={'draft_claims':1,'resolved_claims':1,'verified_claims':1}

def test_rejected_generation_never_becomes_unverified_excerpts(client,library,monkeypatch):
    monkeypatch.setattr(settings(),'generation_provider','gemini')
    monkeypatch.setattr('app.providers.generate',lambda *_:{'claims':[]})
    result=client.post('/api/v1/questions',json={'query':'traditional knowledge patent formulation','cloud_consent':True}).json()
    assert result['mode']=='abstention' and not result['claims'] and not result['citations']
    assert result['metrics']['generation_attempted']
    assert any('could not be verified' in text for text in result['limitations'])
