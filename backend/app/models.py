from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Integer, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default='user')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class Session(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)

class Source(Base):
    __tablename__ = 'sources'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    publisher: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str] = mapped_column(String(20), index=True)
    market: Mapped[str] = mapped_column(String(20), default='treaties')
    language: Mapped[str] = mapped_column(String(5), default='en')
    authority: Mapped[str] = mapped_column(String(25), default='guidance')
    category: Mapped[str] = mapped_column(String(60))
    disposition: Mapped[str] = mapped_column(String(30), default='pending')
    notes: Mapped[str] = mapped_column(Text, default='')
    checked_at: Mapped[datetime | None] = mapped_column(DateTime)
    access: Mapped[str] = mapped_column(String(40), default='public')

class SourceVersion(Base):
    __tablename__ = 'source_versions'
    __table_args__ = (UniqueConstraint('source_id', 'checksum'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id', ondelete='CASCADE'), index=True)
    checksum: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    effective_from: Mapped[str | None] = mapped_column(String(10))
    effective_to: Mapped[str | None] = mapped_column(String(10))
    publication_date: Mapped[str | None] = mapped_column(String(10))
    review_status: Mapped[str] = mapped_column(String(30), default='pending')
    review_note: Mapped[str] = mapped_column(Text, default='')
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    quality: Mapped[dict] = mapped_column(JSON, default=dict)
    supersedes: Mapped[str | None] = mapped_column(String(36))

class Chunk(Base):
    __tablename__ = 'chunks'
    __table_args__ = (UniqueConstraint('version_id', 'ordinal'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    version_id: Mapped[str] = mapped_column(ForeignKey('source_versions.id', ondelete='CASCADE'), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    heading: Mapped[str] = mapped_column(Text, default='')
    locator: Mapped[str] = mapped_column(Text, default='')
    page: Mapped[int | None] = mapped_column(Integer)
    start_offset: Mapped[int] = mapped_column(Integer, default=0)
    end_offset: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(JSON)

class CorpusRelease(Base):
    __tablename__ = 'corpus_releases'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100))
    version_ids: Mapped[list] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    review_note: Mapped[str] = mapped_column(Text, default='')

class GraphEdge(Base):
    __tablename__ = 'graph_edges'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    subject: Mapped[str] = mapped_column(String(200), index=True)
    predicate: Mapped[str] = mapped_column(String(80))
    object: Mapped[str] = mapped_column(String(200))
    evidence_chunk_id: Mapped[str] = mapped_column(ForeignKey('chunks.id', ondelete='CASCADE'))
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

class Case(Base):
    __tablename__ = 'cases'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(180))
    jurisdiction: Mapped[str] = mapped_column(String(20))
    market: Mapped[str] = mapped_column(String(20), default='treaties')
    confidential: Mapped[bool] = mapped_column(Boolean, default=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class PrivateDocument(Base):
    __tablename__ = 'private_documents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(180))
    path: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class Assessment(Base):
    __tablename__ = 'assessments'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str] = mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    rule_version: Mapped[str] = mapped_column(String(30), default='2026.09-pilot.1')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class AnswerTrace(Base):
    __tablename__ = 'answer_traces'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    session_id: Mapped[str | None] = mapped_column(ForeignKey('sessions.id', ondelete='SET NULL'))
    query_hash: Mapped[str] = mapped_column(String(64))
    jurisdiction: Mapped[str] = mapped_column(String(20))
    market: Mapped[str] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(5))
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(30))
    release_id: Mapped[str | None] = mapped_column(String(36))
    citation_ids: Mapped[list] = mapped_column(JSON)
    outcome: Mapped[str] = mapped_column(String(40))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class ReviewRequest(Base):
    __tablename__ = 'review_requests'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    case_id: Mapped[str] = mapped_column(ForeignKey('cases.id', ondelete='CASCADE'), index=True)
    shared_content: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default='submitted')
    assigned_to: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    response: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class Consent(Base):
    __tablename__ = 'consents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    scope: Mapped[str] = mapped_column(String(80))
    purpose: Mapped[str] = mapped_column(String(500))
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(80), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default='queued', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

class Feedback(Base):
    __tablename__ = 'feedback'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    trace_id: Mapped[str] = mapped_column(ForeignKey('answer_traces.id', ondelete='CASCADE'))
    rating: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(100))

class EvaluationRun(Base):
    __tablename__ = 'evaluation_runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    dataset_version: Mapped[str] = mapped_column(String(80))
    report: Mapped[dict] = mapped_column(JSON)
