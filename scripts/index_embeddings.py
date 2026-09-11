import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
os.environ['EMBEDDINGS_ENABLED']='true'
os.environ['HF_HOME']=str(ROOT/'data'/'huggingface')
os.environ['EMBEDDING_REVISION']='614241f622f53c4eeff9890bdc4f31cfecc418b3'
from app.db import SessionLocal
from app.corpus import embed_chunks
with SessionLocal() as db:print('Embedded chunks:',embed_chunks(db),flush=True)
