"""Create evidence-backed navigation links, never infer substantive legal obligations."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from sqlalchemy import select
from app.db import SessionLocal
from app.models import Source,SourceVersion,Chunk,GraphEdge
from app.corpus import active_release
TERMS=['traditional knowledge','patent','biological resources','Ayurvedic','registration','international application','benefit sharing','copyright','herbal']
with SessionLocal() as db:
    release=active_release(db);created=0
    if not release:raise SystemExit('Activate a reference release first.')
    for term in TERMS:
        rows=db.execute(select(Chunk,Source).join(SourceVersion,Chunk.version_id==SourceVersion.id).join(Source,SourceVersion.source_id==Source.id)
            .where(Chunk.version_id.in_(release.version_ids),Chunk.text.ilike('%'+term+'%')).limit(4)).all()
        for chunk,source in rows:
            if term.lower() not in chunk.text.lower():continue
            if db.scalar(select(GraphEdge).where(GraphEdge.evidence_chunk_id==chunk.id,GraphEdge.object==term)):continue
            # Verified literal mention only. This does not mean that an obligation is legally reviewed.
            db.add(GraphEdge(subject=source.title[:200],predicate='references',object=term,evidence_chunk_id=chunk.id,reviewed=True));created+=1
    db.commit();print(f'{created} literal-reference navigation links. No legal obligations inferred.')
