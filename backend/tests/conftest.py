import os
import tempfile
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp(prefix='ipsakti-test-'))/'test.db').replace('\\','/')
os.environ['STORAGE_DIR']=tempfile.mkdtemp(prefix='ipsakti-test-files-')
os.environ['GENERATION_PROVIDER']='none'
os.environ['EMBEDDINGS_ENABLED']='false'
os.environ['REQUESTS_PER_MINUTE']='100000'
os.environ['DAILY_REQUEST_LIMIT']='100000'
import pytest
from fastapi.testclient import TestClient
from app.db import Base,engine,SessionLocal
from app.main import app
from app.models import Source,SourceVersion,Chunk,CorpusRelease

@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine)
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        session=c.get('/api/v1/auth/session').json()
        c.headers['X-CSRF-Token']=session['csrf_token']
        yield c

def sign_in(client,email='user@example.com',role='user'):
    result=client.post('/api/v1/auth/register',json={'email':email,'password':'a-long-test-password'}).json()
    client.headers['X-CSRF-Token']=result['csrf_token']
    if role!='user':
        from app.models import User
        with SessionLocal() as db:
            db.get(User,result['user']['id']).role=role;db.commit()
    return result['user']['id']

@pytest.fixture
def library():
    entries=[
        ('in','india','treaties','patents','A traditional knowledge patent formulation cannot be assessed without prior art. Patent examination considers the claimed invention.'),
        ('us','international','us','market_access','Botanical drug development in the United States requires identifying the applicable regulatory route.'),
        ('eu','international','eu','market_access','Herbal medicinal product registration in the European Union has a distinct regulatory framework.'),
        ('uk','international','uk','market_access','Traditional herbal registration in the United Kingdom concerns herbal medicinal products.'),
        ('treaty','international','treaties','pct','The Patent Cooperation Treaty provides an international patent application procedure.'),
    ]
    ids=[]
    with SessionLocal() as db:
        for id,j,m,category,content in entries:
            s=Source(id='fixture-'+id,title='TEST FIXTURE '+id,publisher='TEST ONLY',url='https://www.wipo.int/',jurisdiction=j,market=m,category=category,authority='guidance')
            db.add(s);db.flush();v=SourceVersion(source_id=s.id,checksum=id*32,path='test.txt',review_status='approved',quality={});db.add(v);db.flush()
            db.add(Chunk(version_id=v.id,ordinal=0,text=content,heading='Test fixture',locator='Fixture paragraph'));ids.append(v.id)
        db.add(CorpusRelease(name='TEST FIXTURES ONLY',version_ids=ids,active=True));db.commit()
    return ids
