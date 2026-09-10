import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy.orm import Session as DBSession
from .config import settings
from .db import get_db
from .models import Session, User, AuditEvent, now

passwords = PasswordHash.recommended()

def digest(value: str) -> str:
    return hmac.new(settings().session_secret.encode(), value.encode(), hashlib.sha256).hexdigest()

def audit(db, action, actor=None, resource=None, **details):
    db.add(AuditEvent(action=action, actor_id=actor, resource_id=resource, details=details))

def issue_session(db, response: Response, user_id=None):
    token, csrf = secrets.token_urlsafe(40), secrets.token_urlsafe(32)
    hours = 168 if user_id else settings().guest_retention_hours
    session = Session(id=digest(token), user_id=user_id, csrf_hash=digest(csrf), expires_at=now()+timedelta(hours=hours))
    db.add(session)
    db.commit()
    response.set_cookie('ipsakti_session', token, httponly=True, secure=settings().cookie_secure, samesite='lax', max_age=hours*3600, path='/')
    return session, csrf

def current_session(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get('ipsakti_session', '')
    session = db.get(Session, digest(token)) if token else None
    if not session or session.expires_at <= now():
        raise HTTPException(401, 'Start a new session.')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        csrf = request.headers.get('X-CSRF-Token', '')
        if not csrf or not hmac.compare_digest(digest(csrf), session.csrf_hash):
            raise HTTPException(403, 'Invalid CSRF token. Refresh your session.')
    return session

def current_user(session: Session = Depends(current_session), db: DBSession = Depends(get_db)):
    user = db.get(User, session.user_id) if session.user_id else None
    if not user: raise HTTPException(401, 'Sign in to use this feature.')
    return user

def roles(*allowed):
    def check(user: User = Depends(current_user)):
        if user.role not in allowed: raise HTTPException(403, 'This role cannot perform that action.')
        return user
    return check

def owned_case(db, case_id, user_id):
    from .models import Case
    case = db.get(Case, case_id)
    if not case or case.user_id != user_id: raise HTTPException(404, 'Case not found.')
    return case
