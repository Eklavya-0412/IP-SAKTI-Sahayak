import pytest
from app import providers,retrieval
from app.db import SessionLocal
from app.schemas import Question
from app.assistant import answer_question

@pytest.mark.parametrize('query',['आयुर्वेदिक पेटेंट कानून गढ़ो।','आयुर्वेदिक पेटंट कायदा 2099 स्पष्ट करा.','Explain the herbal patent rules of 2099.'])
def test_unverified_authority_abstention(client,library,query):
    result=client.post('/api/v1/questions',json={'query':query}).json()
    assert result['mode']=='abstention' and not result['citations']

def test_embedding_outage_falls_back_to_lexical(library,monkeypatch):
    def unavailable():raise RuntimeError('model unavailable')
    monkeypatch.setattr(retrieval,'encoder',unavailable)
    with SessionLocal() as db:
        answer=answer_question(db,Question(query='traditional knowledge patent'))
        assert answer.mode=='retrieval'
        assert answer.metrics['embedding_error']=='RuntimeError'

@pytest.mark.parametrize('raw',[None,'claims',{'claims':'not a list'}])
def test_malformed_draft_is_not_released(library,monkeypatch,raw):
    monkeypatch.setattr(providers,'generate',lambda *args,**kwargs:{'claims':raw})
    with SessionLocal() as db:
        rows,_=retrieval.retrieve(db,'traditional knowledge patent','india')
        assert providers.draft_and_verify('patent',[retrieval.citation(r) for r in rows],'india','treaties')==[]

def test_private_facts_blocked_before_hosted_generation(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings(),'generation_provider','groq')
    with pytest.raises(providers.PrivacyBlocked):providers.draft_and_verify('patent',[],'india','treaties',private_facts=[{'text':'private'}])

def test_empty_html_requires_review(tmp_path):
    from app.corpus import extract_html
    path=tmp_path/'empty.html';path.write_text('<html><body><script>loading()</script></body></html>')
    _,quality=extract_html(path)
    assert quality['requires_review']
