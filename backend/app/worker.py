"""Single-purpose worker; PostgreSQL SKIP LOCKED supports multiple workers safely."""
import json
import time
from datetime import timedelta
from pathlib import Path
from sqlalchemy import select, delete
from .db import SessionLocal
from .models import Job, Session, Case, PrivateDocument, AuditEvent, AnswerTrace, now
from .config import settings
from .corpus import load_manifest, ingest, embed_chunks

def purge(db):
    cfg=settings(); expired=db.scalars(select(Case).where(Case.updated_at<now()-timedelta(days=cfg.case_retention_days))).all()
    for case in expired:
        for doc in db.scalars(select(PrivateDocument).where(PrivateDocument.case_id==case.id)):
            path=Path(doc.path).resolve()
            if path.is_relative_to(cfg.storage_dir.resolve()): path.unlink(missing_ok=True)
        db.delete(case)
    db.execute(delete(Session).where(Session.expires_at<now()))
    db.execute(delete(AnswerTrace).where(AnswerTrace.created_at<now()-timedelta(days=cfg.audit_retention_days)))
    db.execute(delete(AuditEvent).where(AuditEvent.created_at<now()-timedelta(days=cfg.audit_retention_days)))
    db.commit();return {'expired_cases':len(expired)}

def run_once():
    with SessionLocal() as db:
        stale=db.scalars(select(Job).where(Job.status=='running',Job.started_at<now()-timedelta(minutes=15))).all()
        for job in stale:
            job.status='queued' if job.attempts<3 else 'failed'
        db.commit()
        statement=select(Job).where(Job.status=='queued').order_by(Job.created_at).limit(1).with_for_update(skip_locked=True)
        job=db.scalar(statement)
        if not job:return False
        job.status='running';job.started_at=now();job.attempts+=1;db.commit()
        try:
            if job.kind=='ingest':
                manifest=load_manifest(db)
                entry=next(s for s in manifest['sources'] if s['id']==job.payload['source_id'])
                result=ingest(db,entry,job.payload.get('ocr',False))
            elif job.kind=='embed':result={'embedded':embed_chunks(db)}
            elif job.kind=='purge':result=purge(db)
            else:raise ValueError('Unsupported job kind')
            job.status='completed';job.result=result
        except Exception as error:
            db.rollback(); job=db.get(Job,job.id);job.status='failed';job.result={'error':type(error).__name__,'message':str(error)[:250]}
        job.finished_at=now();db.commit()
        return True

def schedule_daily():
    with SessionLocal() as db:
        cutoff=now()-timedelta(hours=24)
        if db.scalar(select(Job.id).where(Job.kind=='purge',Job.created_at>cutoff)):return
        manifest=load_manifest(db)
        db.add(Job(kind='purge'))
        for entry in manifest['sources']:
            if not entry.get('local_path') and entry.get('disposition') not in ('excluded','pointer','background'):
                db.add(Job(kind='ingest',payload={'source_id':entry['id']}))
        db.commit()

def main():
    while True:
        schedule_daily()
        if not run_once():time.sleep(5)

if __name__=='__main__':main()
