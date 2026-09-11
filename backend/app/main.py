import base64
import hashlib
import io
import json
import re
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Literal
from uuid import uuid4
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import Session as DBSession
from .config import settings
from .db import get_db, SessionLocal, engine
from .models import User, Session, Source, SourceVersion, Chunk, CorpusRelease, Case, PrivateDocument, Assessment, ReviewRequest, Consent, GraphEdge, Job, Feedback, AuditEvent, AnswerTrace, EvaluationRun, now
from .schemas import Question, Answer, Credentials, CaseInput, AssessmentInput, ConsentInput, Language
from .security import issue_session, current_session, current_user, roles, owned_case, passwords, digest, audit
from .assistant import answer_question
from .assessments import classify, assess_abs
from .providers import capabilities, bhashini, PrivacyBlocked, ProviderUnavailable
from .retrieval import retrieve, citation
from .corpus import load_manifest, bootstrap_local_reference_corpus, active_release, extract_html, split_plain_text

cfg=settings()

@asynccontextmanager
async def lifespan(app):
    cfg.validate_deployment()
    with SessionLocal() as db:
        load_manifest(db)
        bootstrap_local_reference_corpus(db)
        if cfg.admin_email and cfg.admin_password and not db.scalar(select(User).where(User.email==cfg.admin_email.lower())):
            if len(cfg.admin_password)<12: raise RuntimeError('ADMIN_PASSWORD must contain at least 12 characters.')
            db.add(User(email=cfg.admin_email.lower(),password_hash=passwords.hash(cfg.admin_password),role='admin'));db.commit()
    yield

app=FastAPI(title='IP-SAKTI Sahayak API',version='1.0.0',description='Source-grounded Ayurveda IP and regulatory information. Not legal advice.',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=cfg.trusted_origins,allow_credentials=True,
    allow_methods=['GET','POST','PUT','PATCH','DELETE'],allow_headers=['Content-Type','X-CSRF-Token'])
PREFIX='/api/v1'
requests=defaultdict(deque)

@app.get('/')
def root():
    return {'name': 'IP-SAKTI Sahayak API', 'status': 'ok', 'health': PREFIX + '/health', 'docs': '/docs'}

@app.middleware('http')
async def security_headers(request:Request,call_next):
    if request.method in ('POST','PUT','PATCH','DELETE'):
        origin=request.headers.get('origin')
        if origin and origin not in cfg.trusted_origins:
            return Response('Untrusted request origin',status_code=403)
        length=request.headers.get('content-length')
        if length and not length.isdigit():
            return Response('Invalid content length',status_code=400)
        if length and int(length)>cfg.max_upload_mb*1024*1024+100000:
            return Response('Request too large',status_code=413)
        # One API process by default. A shared gateway limiter is required before scaling replicas.
        identity=digest(request.cookies.get('ipsakti_session') or (request.client.host if request.client else 'unknown'))
        bucket=requests[identity]; tick=time.monotonic()
        while bucket and bucket[0]<tick-60:bucket.popleft()
        if len(bucket)>=cfg.requests_per_minute:
            return Response('Request rate exceeded. Retry in one minute.',status_code=429,headers={'Retry-After':'60'})
        bucket.append(tick)
        if len(requests)>10000:
            for key in list(requests):
                if not requests[key] or requests[key][-1]<tick-60: requests.pop(key,None)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Cache-Control']='no-store'
    if cfg.cookie_secure:response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    return response

@app.get(PREFIX+'/health')
def health(db:DBSession=Depends(get_db)):
    db.execute(select(1))
    return {'status':'ok','database':engine.dialect.name,'version':'1.0.0'}

@app.get(PREFIX+'/capabilities')
def provider_capabilities():return capabilities()

@app.get(PREFIX+'/auth/session')
def session_info(request:Request,response:Response,db:DBSession=Depends(get_db)):
    token=request.cookies.get('ipsakti_session','')
    session=db.get(Session,digest(token)) if token else None
    if not session or session.expires_at<=now():session,csrf=issue_session(db,response)
    else:
        csrf=digest('csrf:'+token);session.csrf_hash=digest(csrf);db.commit()
    user=db.get(User,session.user_id) if session.user_id else None
    return {'csrf_token':csrf,'user':{'id':user.id,'email':user.email,'role':user.role} if user else None,'expires_at':session.expires_at.isoformat()}

@app.post(PREFIX+'/auth/register',status_code=201)
def register(body:Credentials,response:Response,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    email=body.email.lower()
    if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,'An account already exists. Sign in instead.')
    user=User(email=email,password_hash=passwords.hash(body.password));db.add(user);db.flush();audit(db,'account.created',user.id)
    db.delete(session);db.commit();_,csrf=issue_session(db,response,user.id)
    return {'user':{'id':user.id,'email':user.email,'role':user.role},'csrf_token':csrf}

@app.post(PREFIX+'/auth/login')
def login(body:Credentials,response:Response,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==body.email.lower()))
    if not user or not passwords.verify(body.password,user.password_hash):
        audit(db,'login.failed',digest(body.email.lower()));db.commit();raise HTTPException(401,'Email or password is incorrect.')
    db.delete(session);audit(db,'login.succeeded',user.id);db.commit();_,csrf=issue_session(db,response,user.id)
    return {'user':{'id':user.id,'email':user.email,'role':user.role},'csrf_token':csrf}

@app.post(PREFIX+'/auth/logout')
def logout(response:Response,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    db.delete(session);db.commit();response.delete_cookie('ipsakti_session');return {'ok':True}

def validate_question(db,q,session):
    if q.case_id:
        if not session.user_id:raise HTTPException(401,'Sign in to use a case.')
        case=owned_case(db,q.case_id,session.user_id)
        if case.jurisdiction!=q.jurisdiction or case.market!=q.market:raise HTTPException(409,'Case jurisdiction and market do not match this question.')
        q.confidential=q.confidential or case.confidential
    count=db.scalar(select(func.count()).select_from(AnswerTrace).where(AnswerTrace.session_id==session.id,AnswerTrace.created_at>now()-timedelta(days=1)))
    if count>=cfg.daily_request_limit:raise HTTPException(429,'Daily session question limit reached.')

@app.post(PREFIX+'/questions',response_model=Answer)
def question(body:Question,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    validate_question(db,body,session)
    result=answer_question(db,body,session.id)
    if body.case_id:
        case=owned_case(db,body.case_id,session.user_id)
        content=dict(case.content); history=list(content.get('history',[]))[-49:]
        history.append({'question':body.query,'answer':result.model_dump()});content['history']=history
        case.content=content;case.updated_at=now();db.commit()
    return result

@app.post(PREFIX+'/questions/stream')
def stream_question(body:Question,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    validate_question(db,body,session)
    # The worker owns its DB session; no request-scoped session crosses threads.
    import queue
    from concurrent.futures import ThreadPoolExecutor
    session_id = session.id
    def stream():
        events = queue.Queue(maxsize=64)
        def run():
            try:
                with SessionLocal() as thread_db:
                    result = answer_question(thread_db, body, session_id,
                        on_stage=lambda stage: events.put(('stage', {'stage': stage})))
                    if body.case_id:
                        case = owned_case(thread_db, body.case_id, thread_db.get(Session, session_id).user_id)
                        content = dict(case.content)
                        content['history'] = list(content.get('history', []))[-49:] + [{'question': body.query, 'answer': result.model_dump()}]
                        case.content = content
                        case.updated_at = now()
                        thread_db.commit()
                    events.put(('answer', result.model_dump()))
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Question stream failed')
                events.put(('error', {'message': 'Question processing failed. Please retry.'}))
            finally:
                events.put(None)
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(run)
            yield 'event: stage\ndata: {"stage":"Searching and verifying sources"}\n\n'
            while True:
                try:
                    item = events.get(timeout=15)
                except queue.Empty:
                    yield ': keep-alive\n\n'
                    continue
                if item is None:
                    break
                event, data = item
                yield f'event: {event}\ndata: {json.dumps(data)}\n\n'
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'X-Accel-Buffering':'no','Cache-Control':'no-cache'})

@app.post(PREFIX+'/questions/compare')
def compare(body:Question,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    if body.case_id:raise HTTPException(422,'Compare without a case to keep jurisdiction histories separate.')
    validate_question(db,body,session)
    return {'india':answer_question(db,body.model_copy(update={'jurisdiction':'india','market':'treaties'}),session.id),
            'international':answer_question(db,body.model_copy(update={'jurisdiction':'international'}),session.id)}

@app.post(PREFIX+'/assessments/{kind}')
def assessment(kind:Literal['classification','abs'],body:AssessmentInput,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    record=db.get(Assessment,body.assessment_id) if body.assessment_id else None
    if body.assessment_id and (not record or record.session_id!=session.id or record.kind!=kind):raise HTTPException(404,'Assessment not found.')
    if not record:record=Assessment(session_id=session.id,kind=kind,answers={});db.add(record);db.flush()
    answers={**record.answers,**body.answers}
    try:result=(classify if kind=='classification' else assess_abs)(db,answers,body.language)
    except ValueError as error:raise HTTPException(422,str(error))
    from .localization import localize_explanations
    record.answers=answers;db.commit();return {'assessment_id':record.id,'answers':answers,**localize_explanations(result,body.language)}

@app.get(PREFIX+'/sources')
def sources(query:str='',jurisdiction:Literal['india','international']|None=None,market:str|None=None,db:DBSession=Depends(get_db)):
    statement=select(Source).order_by(Source.title)
    if jurisdiction:statement=statement.where(Source.jurisdiction==jurisdiction)
    if market:statement=statement.where(Source.market==market)
    if query:statement=statement.where(Source.title.ilike('%'+query[:150]+'%'))
    rows=[]
    for s in db.scalars(statement):
        versions=db.scalars(select(SourceVersion).where(SourceVersion.source_id==s.id).order_by(SourceVersion.retrieved_at.desc())).all()
        rows.append({'id':s.id,'title':s.title,'url':s.url,'publisher':s.publisher,'jurisdiction':s.jurisdiction,'market':s.market,
            'category':s.category,'authority':s.authority,'language':s.language,'disposition':s.disposition,'notes':s.notes,'access':s.access,
            'checked_at':s.checked_at.isoformat() if s.checked_at else None,
            'versions':[{'id':v.id,'checksum':v.checksum,'review_status':v.review_status,'quality':v.quality,
                'retrieved_at':v.retrieved_at.isoformat(),'effective_from':v.effective_from,'review_note':v.review_note} for v in versions]})
    return rows

@app.get(PREFIX+'/sources/search')
def search_sources(query:str=Query(min_length=2,max_length=1000),jurisdiction:Literal['india','international']='india',market:str='treaties',db:DBSession=Depends(get_db)):
    rows,metrics=retrieve(db,query,jurisdiction,'treaties' if jurisdiction=='india' else market)
    return {'citations':[citation(r) for r in rows],'metrics':metrics}

@app.get(PREFIX+'/sources/chunks/{chunk_id}')
def source_chunk(chunk_id:str,db:DBSession=Depends(get_db)):
    chunk=db.get(Chunk,chunk_id)
    if not chunk:raise HTTPException(404,'Excerpt not found.')
    version=db.get(SourceVersion,chunk.version_id);source=db.get(Source,version.source_id)
    return {**citation((chunk,version,source)).model_dump(),'heading':chunk.heading,'start_offset':chunk.start_offset,'end_offset':chunk.end_offset,
        'checksum':version.checksum,'review_note':version.review_note,'file_url':PREFIX+'/sources/versions/'+version.id+'/file'}

@app.get(PREFIX+'/sources/versions/{version_id}/file')
def source_file(version_id:str,db:DBSession=Depends(get_db)):
    version=db.get(SourceVersion,version_id)
    if not version:raise HTTPException(404,'Source version not found.')
    path=Path(version.path).resolve()
    if not path.is_relative_to((cfg.storage_dir/'snapshots').resolve()) or not path.is_file():raise HTTPException(404,'Snapshot unavailable.')
    # HTML is a download, never active same-origin content.
    return FileResponse(path,media_type='application/pdf' if path.suffix=='.pdf' else 'application/octet-stream',filename=version.source_id+path.suffix,content_disposition_type='attachment')

@app.get(PREFIX+'/coverage')
def coverage(db:DBSession=Depends(get_db)):
    release=active_release(db)
    sources=db.scalars(select(Source)).all()
    versions=db.scalars(select(SourceVersion)).all()
    categories={}
    for s in sources:
        key=f'{s.jurisdiction}:{s.market}:{s.category}'
        group=categories.setdefault(key,{'sources':0,'downloaded':0,'approved':0})
        group['sources']+=1
        group['downloaded']+=any(v.source_id==s.id for v in versions)
        group['approved']+=any(v.source_id==s.id and v.review_status=='approved' and release and v.id in release.version_ids for v in versions)
    return {'release':{'id':release.id,'name':release.name,'review_note':release.review_note} if release else None,
        'sources':len(sources),'versions':len(versions),'chunks':db.scalar(select(func.count()).select_from(Chunk)),
        'approved_versions':sum(v.review_status=='approved' for v in versions),'categories':categories,
        'expert_review':'No expert validation recorded unless attached to an explicit review record.'}

@app.get(PREFIX+'/cases')
def list_cases(user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    return [case_dict(c) for c in db.scalars(select(Case).where(Case.user_id==user.id).order_by(Case.updated_at.desc()))]

def case_dict(c):return {'id':c.id,'title':c.title,'jurisdiction':c.jurisdiction,'market':c.market,'confidential':c.confidential,'content':c.content,'updated_at':c.updated_at.isoformat()}

@app.post(PREFIX+'/cases',status_code=201)
def create_case(body:CaseInput,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    if len(json.dumps(body.content))>200000:raise HTTPException(413,'Case content is too large.')
    values=body.model_dump()
    if body.jurisdiction=='india':values['market']='treaties'
    case=Case(user_id=user.id,**values);db.add(case);db.flush();audit(db,'case.created',user.id,case.id);db.commit();return case_dict(case)

@app.patch(PREFIX+'/cases/{case_id}')
def update_case(case_id:str,body:CaseInput,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    case=owned_case(db,case_id,user.id)
    if len(json.dumps(body.content))>200000:raise HTTPException(413,'Case content is too large.')
    if body.jurisdiction!=case.jurisdiction or (body.jurisdiction=='international' and body.market!=case.market):raise HTTPException(409,'Create a separate case for another jurisdiction.')
    case.title=body.title;case.confidential=body.confidential;case.content=body.content;case.updated_at=now();db.commit();return case_dict(case)

def remove_case(db,case):
    for doc in db.scalars(select(PrivateDocument).where(PrivateDocument.case_id==case.id)):
        path=Path(doc.path).resolve()
        if path.is_relative_to((cfg.storage_dir/'private').resolve()):path.unlink(missing_ok=True)
    db.delete(case)

@app.delete(PREFIX+'/cases/{case_id}')
def delete_case(case_id:str,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    case=owned_case(db,case_id,user.id);remove_case(db,case);audit(db,'case.deleted',user.id,case_id);db.commit();return {'ok':True}

@app.get(PREFIX+'/cases/{case_id}/export')
def export_case(case_id:str,format:Literal['json','pdf']='json',user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    case=owned_case(db,case_id,user.id)
    if format=='json':return case_dict(case)
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from xml.sax.saxutils import escape
    from .pdf_fonts import configure_case_styles
    styles=configure_case_styles(getSampleStyleSheet());buffer=io.BytesIO()
    story=[Paragraph('IP-SAKTI Sahayak: Case brief',styles['Title']),Paragraph(escape(case.title),styles['Heading2']),
        Paragraph(f'Jurisdiction: {case.jurisdiction}; market: {case.market}. Information, not legal advice.',styles['Normal'])]
    for turn in case.content.get('history',[]):
        story.append(Spacer(1,12));story.append(Paragraph(escape(turn.get('question','')),styles['Heading3']))
        answer=turn.get('answer',{})
        for claim in answer.get('claims',[]):story.append(Paragraph(escape(claim.get('text','')),styles['Normal']))
        for cite in answer.get('citations',[]):story.append(Paragraph(escape(f"{cite['title']} | {cite['locator']} | {cite['url']}"),styles['Normal']))
    SimpleDocTemplate(buffer).build(story)
    return Response(buffer.getvalue(),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="case-{case.id}.pdf"'})

@app.post(PREFIX+'/cases/{case_id}/documents',status_code=201)
async def upload_document(case_id:str,file:UploadFile=File(...),permission:bool=Form(False),user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    case=owned_case(db,case_id,user.id)
    if not permission:raise HTTPException(422,'Confirm permission to import this document.')
    ext=Path(file.filename or '').suffix.lower()
    if ext not in ('.pdf','.txt'):raise HTTPException(415,'Only PDF and TXT are supported.')
    body=await file.read(cfg.max_upload_mb*1024*1024+1)
    if len(body)>cfg.max_upload_mb*1024*1024:raise HTTPException(413,'File too large.')
    if ext=='.pdf' and not body.startswith(b'%PDF'):raise HTTPException(415,'Invalid PDF signature.')
    id=str(uuid4());folder=cfg.storage_dir/'private'/user.id/case.id;folder.mkdir(parents=True,exist_ok=True)
    path=folder/(id+ext);path.write_bytes(body)
    try:
        if ext == '.pdf':
            # Private uploads stay local — do NOT call LlamaParse (confidential + API cost).
            # Use a lightweight text extraction via pdfminer/pypdfium if available,
            # otherwise read raw bytes and decode printable chars as a safe fallback.
            try:
                import pypdfium2  # type: ignore
                pdf = pypdfium2.PdfDocument(str(path))
                pages_text = [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
                pdf.close()
                content = '\n'.join(pages_text)
            except ImportError:
                # Minimal fallback: strip binary and keep printable ASCII/Unicode
                raw = body.decode('latin-1', errors='replace')
                content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', raw)
            quality = {'method': 'local_pdf', 'pages': 1, 'requires_review': True}
        else:
            content, quality = extract_html(path)
            content = content  # already plain text
    except Exception:
        path.unlink(missing_ok=True); raise HTTPException(422, 'Document could not be extracted safely.')
    if len(content) > 500000: path.unlink(missing_ok=True); raise HTTPException(413, 'Extracted document exceeds text limit.')
    doc = PrivateDocument(id=id, case_id=case.id, name=Path(file.filename).name[:180], path=str(path), text=content, checksum=hashlib.sha256(body).hexdigest())
    db.add(doc); case.confidential = True; case.updated_at = now(); audit(db, 'document.imported', user.id, id, permission=True); db.commit()
    return {'id': id, 'name': doc.name, 'characters': len(content), 'quality': quality, 'authority': 'private evidence; not public legal authority'}

@app.get(PREFIX+'/cases/{case_id}/documents')
def list_documents(case_id:str,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    owned_case(db,case_id,user.id)
    return [{'id':d.id,'name':d.name,'characters':len(d.text)} for d in db.scalars(select(PrivateDocument).where(PrivateDocument.case_id==case_id))]

class ReviewSubmission(BaseModel):
    summary:str=Field(min_length=10,max_length=10000)
    include_history:bool=False

@app.post(PREFIX+'/cases/{case_id}/review',status_code=201)
def submit_review(case_id:str,body:ReviewSubmission,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    case=owned_case(db,case_id,user.id)
    shared={'title':case.title,'jurisdiction':case.jurisdiction,'market':case.market,'summary':body.summary}
    if body.include_history:shared['history']=case.content.get('history',[])
    review=ReviewRequest(case_id=case.id,shared_content=shared);db.add(review);db.flush();audit(db,'review.submitted',user.id,review.id,history_shared=body.include_history);db.commit()
    return {'id':review.id,'status':review.status,'assigned_to':None,'message':'Submitted; no facilitator assigned yet.'}

def _review_dict(r):
    return {'id':r.id,'case_id':r.case_id,'status':r.status,'assigned_to':r.assigned_to,
        'shared_content':r.shared_content,'response':r.response,
        'created_at':r.created_at.isoformat(),'updated_at':r.updated_at.isoformat() if r.updated_at else r.created_at.isoformat()}

@app.get(PREFIX+'/reviews')
def reviews(user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    statement=select(ReviewRequest)
    if user.role not in ('facilitator','admin'):statement=statement.join(Case).where(Case.user_id==user.id)
    return [_review_dict(r) for r in db.scalars(statement)]

@app.get(PREFIX+'/reviews/{review_id}')
def get_review(review_id:str,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    review=db.get(ReviewRequest,review_id)
    if not review:raise HTTPException(404,'Review not found.')
    # Non-facilitator/admin users can only see their own reviews
    if user.role not in ('facilitator','admin'):
        case=db.get(Case,review.case_id)
        if not case or case.user_id!=user.id:raise HTTPException(404,'Review not found.')
    return _review_dict(review)

class ReviewUpdate(BaseModel):
    status:Literal['assigned','in_review','resolved']
    response:str=Field(default='',max_length=10000)

@app.patch(PREFIX+'/reviews/{review_id}')
def review_update(review_id:str,body:ReviewUpdate,user:User=Depends(roles('facilitator','admin')),db:DBSession=Depends(get_db)):
    review=db.get(ReviewRequest,review_id)
    if not review:raise HTTPException(404,'Review not found.')
    if review.assigned_to not in (None,user.id) and user.role!='admin':raise HTTPException(403,'Assigned to another facilitator.')
    allowed={'submitted':['assigned'],'assigned':['in_review'],'in_review':['resolved'],'resolved':[]}
    valid_transitions=allowed.get(review.status,[])
    if body.status not in valid_transitions:
        raise HTTPException(409,f'Invalid review-state transition: {review.status} → {body.status}. '
            f'Allowed transitions: {valid_transitions or "none (terminal state)"}.')
    if body.status=='resolved' and len(body.response.strip())<10:raise HTTPException(422,'Provide a substantive review response.')
    review.assigned_to=user.id
    review.status=body.status
    review.response=body.response or review.response
    review.updated_at=now()
    audit(db,'review.updated',user.id,review.id,status=body.status);db.commit()
    return _review_dict(review)


@app.get(PREFIX+'/consents')
def list_consents(user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    return [{'id':c.id,'provider':c.provider,'scope':c.scope,'purpose':c.purpose,'expires_at':c.expires_at.isoformat(),'revoked':c.revoked_at is not None} for c in db.scalars(select(Consent).where(Consent.user_id==user.id))]

@app.post(PREFIX+'/consents',status_code=201)
def grant_consent(body:ConsentInput,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    consent=Consent(user_id=user.id,provider=body.provider,scope=body.scope,purpose=body.purpose,expires_at=now()+timedelta(days=body.days))
    db.add(consent);db.flush();audit(db,'consent.granted',user.id,consent.id,provider=body.provider,scope=body.scope);db.commit();return {'id':consent.id,'expires_at':consent.expires_at.isoformat()}

@app.delete(PREFIX+'/consents/{consent_id}')
def revoke_consent(consent_id:str,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    consent=db.get(Consent,consent_id)
    if not consent or consent.user_id!=user.id:raise HTTPException(404,'Consent not found.')
    consent.revoked_at=now();audit(db,'consent.revoked',user.id,consent.id);db.commit();return {'ok':True}

class ConnectorRequest(BaseModel):
    provider:str
    scope:Literal['search','read']
    query:str=Field(max_length=1000)

@app.post(PREFIX+'/connectors/access')
def connector_access(body:ConnectorRequest,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    consent=db.scalar(select(Consent).where(Consent.user_id==user.id,Consent.provider==body.provider,Consent.scope==body.scope,Consent.revoked_at.is_(None),Consent.expires_at>now()))
    if not consent:raise HTTPException(403,'An active scoped consent receipt is required.')
    audit(db,'connector.access_attempt',user.id,consent.id,provider=body.provider,scope=body.scope,result='not_configured');db.commit()
    raise HTTPException(503,'No licensed vendor adapter is configured. Consent does not grant a subscription.')

class LanguageRequest(BaseModel):
    task:Literal['translation','asr','tts']
    source:Language='en'
    target:Language|None=None
    text:str|None=Field(default=None,max_length=12000)
    audio:str|None=Field(default=None,max_length=2200000)
    allow_cloud:bool=False
    confidential:bool=False

@app.post(PREFIX+'/language')
def language(body:LanguageRequest,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    if body.task=='asr':
        try:
            import wave
            raw=base64.b64decode(body.audio or '',validate=True)
            with wave.open(io.BytesIO(raw)) as recording:
                if recording.getnchannels()!=1 or recording.getframerate()!=16000 or recording.getsampwidth()!=2 or recording.getnframes()>16000*60:raise ValueError()
        except Exception:raise HTTPException(422,'Use mono 16 kHz, 16-bit WAV audio, up to 60 seconds.')
    elif not body.text:raise HTTPException(422,'Text is required.')
    try:result=bhashini(**body.model_dump())
    except PrivacyBlocked as error:raise HTTPException(403,str(error))
    except ProviderUnavailable as error:raise HTTPException(503,str(error))
    audit(db,'language.processed',session.user_id or session.id,task=body.task,consented=body.allow_cloud);db.commit();return result

# ── Prior Art Search with extended mock dataset, fuzzy matching, and compound queries ──

_PRIOR_ART_DB = {
    'ashwagandha': {
        'synonyms': ['Withania somnifera', 'winter cherry', 'ashwagandha root', 'Indian ginseng'],
        'citations': [
            {'title': 'WO2018/123456 - Withania somnifera extract composition for adaptogenic use', 'patent': 'WO2018/123456', 'score': 0.93, 'match': 'Strong botanical and formulation overlap with withanolide-standardised extract', 'family': 'botanical extract / adaptogen'},
            {'title': 'IN2020/000123 - Ashwagandha stress-relief tablet formulation with KSM-66', 'patent': 'IN2020/000123', 'score': 0.88, 'match': 'Likely overlap in composition, dosage target, and withanolide concentration', 'family': 'oral tablet / stress relief'},
            {'title': 'US2021/0102345 - Herbal formulation using Withania somnifera for cognitive enhancement', 'patent': 'US2021/0102345', 'score': 0.82, 'match': 'Similar base extract and nootropic therapeutic claims', 'family': 'herbal nutraceutical'},
        ],
        'similarity': [
            {'label': 'Botanical name match', 'score': 0.97},
            {'label': 'Traditional-use overlap (Rasayana / adaptogenic)', 'score': 0.89},
            {'label': 'Formulation similarity (root extract standardisation)', 'score': 0.81},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/ASH-001', 'text': 'Ashwagandha (Withania somnifera) — Rasayana use documented in Charaka Samhita, Chikitsa Sthana'},
            {'id': 'TKDL/AY/ASH-002', 'text': 'Ashwagandha Churna — traditional stress-relief and vitality formulation in Ayurvedic Formulary of India'},
        ],
    },
    'turmeric': {
        'synonyms': ['Curcuma longa', 'haldi', 'curcumin', 'haridra'],
        'citations': [
            {'title': 'US2019/045678 - Curcumin composition for anti-inflammatory use', 'patent': 'US2019/045678', 'score': 0.91, 'match': 'Strong overlap on turmeric species and bioactive curcuminoid component', 'family': 'curcumin composition'},
            {'title': 'IN2017/007890 - Turmeric extract powder dosage formulation for joint health', 'patent': 'IN2017/007890', 'score': 0.84, 'match': 'Similar plant-part extraction and oral delivery route', 'family': 'oral powder / extract'},
            {'title': 'EP2016/334455 - Bioavailable curcumin nanoparticle formulation', 'patent': 'EP2016/334455', 'score': 0.79, 'match': 'Novel delivery system for enhanced curcumin absorption', 'family': 'nanoparticle / bioavailability'},
        ],
        'similarity': [
            {'label': 'Species name match', 'score': 0.95},
            {'label': 'Ingredient overlap (curcuminoids)', 'score': 0.87},
            {'label': 'Delivery route similarity', 'score': 0.75},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/TUR-001', 'text': 'Haridra (Curcuma longa) — wound healing and anti-inflammatory use in Sushruta Samhita'},
            {'id': 'TKDL/AY/TUR-002', 'text': 'Haridra Khanda — classical formulation for skin disorders in Bhaishajya Ratnavali'},
        ],
    },
    'neem': {
        'synonyms': ['Azadirachta indica', 'nimba', 'margosa', 'neem leaf', 'nimb'],
        'citations': [
            {'title': 'EP1996/436789 - Neem oil composition for pest control (revoked)', 'patent': 'EP1996/436789', 'score': 0.90, 'match': 'Azadirachtin-based formulation; patent revoked on traditional knowledge grounds at EPO', 'family': 'biopesticide / agricultural'},
            {'title': 'IN2019/004567 - Neem extract oral formulation for blood sugar management', 'patent': 'IN2019/004567', 'score': 0.85, 'match': 'Overlap in neem leaf extract for metabolic health claims', 'family': 'oral extract / metabolic'},
            {'title': 'US2020/0789012 - Antimicrobial neem bark extract for dental care', 'patent': 'US2020/0789012', 'score': 0.78, 'match': 'Similar antibacterial mechanism using nimbidin compounds', 'family': 'dental / antimicrobial'},
        ],
        'similarity': [
            {'label': 'Botanical name match', 'score': 0.96},
            {'label': 'Traditional-use overlap (Krimighna / antibacterial)', 'score': 0.91},
            {'label': 'Formulation similarity', 'score': 0.74},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/NIM-001', 'text': 'Nimba (Azadirachta indica) — Krimighna and Kushthaghna properties documented in Charaka Samhita'},
            {'id': 'TKDL/AY/NIM-002', 'text': 'EP patent on neem fungicidal use opposed and revoked using TKDL evidence (landmark case)'},
        ],
    },
    'tulsi': {
        'synonyms': ['Ocimum tenuiflorum', 'Ocimum sanctum', 'holy basil', 'tulasi', 'sacred basil'],
        'citations': [
            {'title': 'IN2018/002345 - Tulsi extract standardised for ursolic acid content', 'patent': 'IN2018/002345', 'score': 0.87, 'match': 'Overlap in Ocimum sanctum extract with phytochemical standardisation', 'family': 'standardised extract'},
            {'title': 'WO2020/567890 - Holy basil adaptogenic and immunomodulatory composition', 'patent': 'WO2020/567890', 'score': 0.83, 'match': 'Similar immunomodulatory therapeutic claims using tulsi', 'family': 'adaptogen / immunomodulator'},
        ],
        'similarity': [
            {'label': 'Species name match', 'score': 0.94},
            {'label': 'Traditional-use overlap (Rasayana / respiratory)', 'score': 0.86},
            {'label': 'Therapeutic claim similarity', 'score': 0.79},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/TUL-001', 'text': 'Tulasi (Ocimum sanctum) — Shwasahara and Kasahara use in Bhavaprakasha Nighantu'},
        ],
    },
    'giloy': {
        'synonyms': ['Tinospora cordifolia', 'guduchi', 'amrita', 'giloya', 'heart-leaved moonseed'],
        'citations': [
            {'title': 'IN2021/005678 - Guduchi extract tablet for immunomodulation', 'patent': 'IN2021/005678', 'score': 0.86, 'match': 'Overlap in Tinospora cordifolia stem extract for immune support', 'family': 'immunomodulator / oral tablet'},
            {'title': 'WO2019/890123 - Tinospora-based composition for fever management', 'patent': 'WO2019/890123', 'score': 0.81, 'match': 'Similar Jwarahara (antipyretic) claim using guduchi', 'family': 'antipyretic / herbal'},
        ],
        'similarity': [
            {'label': 'Botanical name match', 'score': 0.95},
            {'label': 'Traditional-use overlap (Rasayana / Jwarahara)', 'score': 0.88},
            {'label': 'Formulation similarity', 'score': 0.76},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/GUD-001', 'text': 'Guduchi (Tinospora cordifolia) — Rasayana and Jwarahara use documented in Charaka Samhita and Ashtanga Hridaya'},
        ],
    },
    'shatavari': {
        'synonyms': ['Asparagus racemosus', 'shatavari root', 'satavar', 'wild asparagus'],
        'citations': [
            {'title': 'IN2020/006789 - Shatavari root extract for lactation support', 'patent': 'IN2020/006789', 'score': 0.85, 'match': 'Overlap in galactagogue claims using Asparagus racemosus saponins', 'family': 'galactagogue / women health'},
            {'title': 'US2022/0234567 - Asparagus racemosus adaptogenic formulation for hormonal balance', 'patent': 'US2022/0234567', 'score': 0.80, 'match': 'Similar phytoestrogenic and adaptogenic claims', 'family': 'adaptogen / hormonal'},
        ],
        'similarity': [
            {'label': 'Botanical name match', 'score': 0.96},
            {'label': 'Traditional-use overlap (Stanya-janana / galactagogue)', 'score': 0.87},
            {'label': 'Formulation similarity', 'score': 0.73},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/SHA-001', 'text': 'Shatavari (Asparagus racemosus) — Stanya-janana and Balya use documented in Dhanvantari Nighantu'},
        ],
    },
    'brahmi': {
        'synonyms': ['Bacopa monnieri', 'water hyssop', 'brahmi leaf', 'Centella asiatica', 'gotu kola', 'mandukaparni'],
        'citations': [
            {'title': 'US2018/0345678 - Bacopa monnieri extract standardised for bacosides', 'patent': 'US2018/0345678', 'score': 0.89, 'match': 'Strong overlap in nootropic claims and bacoside standardisation', 'family': 'nootropic / cognitive'},
            {'title': 'IN2019/007890 - Brahmi-based memory enhancement syrup formulation', 'patent': 'IN2019/007890', 'score': 0.84, 'match': 'Similar Medhya Rasayana claims in oral liquid format', 'family': 'syrup / cognitive enhancement'},
            {'title': 'EP2021/112233 - Centella asiatica triterpene extract for neuroprotection', 'patent': 'EP2021/112233', 'score': 0.77, 'match': 'Related botanical (Mandukaparni) with overlapping CNS claims', 'family': 'neuroprotective'},
        ],
        'similarity': [
            {'label': 'Botanical name match', 'score': 0.93},
            {'label': 'Traditional-use overlap (Medhya Rasayana / cognitive)', 'score': 0.90},
            {'label': 'Formulation similarity (bacoside standardisation)', 'score': 0.82},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/BRA-001', 'text': 'Brahmi (Bacopa monnieri) — Medhya Rasayana use in Charaka Samhita, Chikitsa Sthana Ch.1'},
            {'id': 'TKDL/AY/BRA-002', 'text': 'Brahmi Ghrita — classical formulation for intellect enhancement in Ashtanga Hridaya'},
        ],
    },
    'triphala': {
        'synonyms': ['triphala churna', 'three fruits', 'amalaki haritaki bibhitaki', 'Emblica Terminalia'],
        'citations': [
            {'title': 'IN2017/008901 - Triphala formulation with enhanced bioavailability', 'patent': 'IN2017/008901', 'score': 0.86, 'match': 'Overlap in classical three-fruit combination with modified delivery', 'family': 'digestive / antioxidant'},
            {'title': 'WO2021/445566 - Triphala-based oral care composition', 'patent': 'WO2021/445566', 'score': 0.80, 'match': 'Similar antimicrobial application of triphala tannins', 'family': 'oral care / antimicrobial'},
        ],
        'similarity': [
            {'label': 'Formulation name match', 'score': 0.97},
            {'label': 'Traditional-use overlap (Tridoshahara / digestive)', 'score': 0.91},
            {'label': 'Ingredient composition match', 'score': 0.88},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/TRI-001', 'text': 'Triphala — classical Tridoshahara formulation (Amalaki + Haritaki + Bibhitaki) in Charaka Samhita and Sushruta Samhita'},
        ],
    },
    'guggulu': {
        'synonyms': ['Commiphora wightii', 'guggul', 'Indian bdellium', 'mukul myrrh', 'guggulipid'],
        'citations': [
            {'title': 'US2003/0012345 - Guggulsterone composition for cholesterol management', 'patent': 'US2003/0012345', 'score': 0.88, 'match': 'Strong overlap in guggulsterone E/Z isomers for lipid-lowering claims', 'family': 'lipid-lowering / cardiovascular'},
            {'title': 'IN2018/009012 - Yograj Guggulu tablet with standardised extract', 'patent': 'IN2018/009012', 'score': 0.83, 'match': 'Classical Yograj Guggulu formulation with modern tablet technology', 'family': 'anti-inflammatory / classical'},
            {'title': 'WO2020/778899 - Guggul resin fraction for anti-arthritic application', 'patent': 'WO2020/778899', 'score': 0.79, 'match': 'Related oleoresin extraction with joint-health claims', 'family': 'anti-arthritic / botanical'},
        ],
        'similarity': [
            {'label': 'Botanical name match', 'score': 0.94},
            {'label': 'Traditional-use overlap (Medohara / lipid-lowering)', 'score': 0.89},
            {'label': 'Active compound match (guggulsterones)', 'score': 0.85},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/GUG-001', 'text': 'Guggulu (Commiphora wightii) — Medohara and Vatahara properties in Sushruta Samhita'},
            {'id': 'TKDL/AY/GUG-002', 'text': 'Yograj Guggulu — classical anti-inflammatory formulation in Bhaishajya Ratnavali'},
        ],
    },
    'amla': {
        'synonyms': ['Phyllanthus emblica', 'Emblica officinalis', 'amalaki', 'Indian gooseberry', 'amala'],
        'citations': [
            {'title': 'IN2019/010123 - Amla extract standardised for vitamin C and tannins', 'patent': 'IN2019/010123', 'score': 0.87, 'match': 'Overlap in Phyllanthus emblica fruit extract standardisation for antioxidant use', 'family': 'antioxidant / vitamin C'},
            {'title': 'US2021/0456789 - Amalaki-based anti-ageing topical composition', 'patent': 'US2021/0456789', 'score': 0.82, 'match': 'Similar polyphenol-rich extract for dermatological anti-ageing claims', 'family': 'topical / anti-ageing'},
        ],
        'similarity': [
            {'label': 'Botanical name match', 'score': 0.96},
            {'label': 'Traditional-use overlap (Rasayana / Vayasthapana)', 'score': 0.88},
            {'label': 'Phytochemical profile similarity', 'score': 0.80},
        ],
        'tkdl_references': [
            {'id': 'TKDL/AY/AML-001', 'text': 'Amalaki (Phyllanthus emblica) — Rasayana and Vayasthapana use documented in Charaka Samhita'},
            {'id': 'TKDL/AY/AML-002', 'text': 'Chyawanprash — classical Rasayana formulation with Amalaki as primary ingredient in Charaka Samhita'},
        ],
    },
}

# Build reverse lookup for fuzzy matching: all synonyms and alternate names
_PRIOR_ART_ALIASES = {}
for _key, _data in _PRIOR_ART_DB.items():
    _PRIOR_ART_ALIASES[_key] = _key
    for _syn in _data['synonyms']:
        _PRIOR_ART_ALIASES[_syn.lower()] = _key


def _fuzzy_match_herb(term):
    """Try exact match first, then fuzzy match against known herb names and synonyms."""
    import difflib
    normalized = term.strip().lower()
    # Exact match on key or synonym
    if normalized in _PRIOR_ART_ALIASES:
        return _PRIOR_ART_DB[_PRIOR_ART_ALIASES[normalized]]
    # Fuzzy match
    candidates = list(_PRIOR_ART_ALIASES.keys())
    matches = difflib.get_close_matches(normalized, candidates, n=1, cutoff=0.6)
    if matches:
        return _PRIOR_ART_DB[_PRIOR_ART_ALIASES[matches[0]]]
    return None


@app.get(PREFIX+'/prior-art')
def prior_art(term:str=Query(min_length=2,max_length=150)):
    normalized = term.strip().lower()
    # Detect compound/multi-ingredient queries
    parts = re.split(r'[+,&]|\band\b|\s+and\s+', normalized)
    parts = [p.strip() for p in parts if len(p.strip()) >= 2]

    if len(parts) > 1:
        # Compound query: merge results from multiple herbs
        all_citations = []
        all_similarity = []
        all_synonyms = []
        all_tkdl = []
        matched_names = []
        for part in parts[:4]:  # limit to 4 ingredients
            entry = _fuzzy_match_herb(part)
            if entry:
                matched_names.append(part)
                all_citations.extend(entry['citations'])
                all_similarity.extend(entry['similarity'])
                all_synonyms.extend(entry['synonyms'])
                all_tkdl.extend(entry.get('tkdl_references', []))
        if not all_citations:
            # None of the parts matched, fall through to single-term logic
            entry = None
        else:
            # De-duplicate citations by patent number
            seen_patents = set()
            unique_citations = []
            for c in all_citations:
                if c['patent'] not in seen_patents:
                    seen_patents.add(c['patent'])
                    unique_citations.append(c)
            entry = {
                'synonyms': list(dict.fromkeys(all_synonyms)),
                'citations': unique_citations[:8],
                'similarity': [
                    {'label': f'Compound formulation overlap ({" + ".join(matched_names)})', 'score': 0.85},
                    {'label': 'Individual ingredient match (averaged)', 'score': round(sum(s['score'] for s in all_similarity) / max(len(all_similarity), 1), 2)},
                    {'label': 'Synergistic combination novelty risk', 'score': 0.70},
                ],
                'tkdl_references': list({r['id']: r for r in all_tkdl}.values()),
            }
    else:
        entry = _fuzzy_match_herb(normalized)

    if entry is None:
        entry = {
            'synonyms': [term],
            'citations': [
                {'title': f'{term.title()} — general concept-level prior art search', 'patent': 'SEARCH-REQUIRED', 'score': 0.72,
                 'match': 'No pre-indexed data available for this term. Perform a full prior art search using the links below.', 'family': 'concept review'},
            ],
            'similarity': [
                {'label': 'Keyword overlap', 'score': 0.70},
                {'label': 'Botanical/ingredient plausibility', 'score': 0.64},
                {'label': 'Therapeutic route similarity', 'score': 0.58},
            ],
            'tkdl_references': [],
        }
    words = [term] + entry['synonyms']
    return {
        'term': term,
        'terms': list(dict.fromkeys(words))[:10],
        'queries': [
            ' OR '.join('"' + w.replace('"', '') + '"' for w in words),
            '(' + ' OR '.join(words) + ') AND (extract OR composition OR formulation OR traditional medicine)',
            '(' + ' OR '.join(words) + ') AND (oral OR tablet OR capsule OR syrup)',
            '(' + ' OR '.join(words) + ') AND (patent OR intellectual property OR prior art OR TKDL)',
        ],
        'citations': entry['citations'],
        'similarity_breakdown': entry['similarity'],
        'tkdl_references': entry.get('tkdl_references', []),
        'links': [
            {'title': 'IP India: Patent search entry point', 'url': 'https://ipindia.gov.in/'},
            {'title': 'WIPO PATENTSCOPE', 'url': 'https://patentscope.wipo.int/'},
            {'title': 'TKDL: public information and access', 'url': 'https://www.tkdl.res.in/'},
            {'title': 'Google Patents', 'url': 'https://patents.google.com/'},
            {'title': 'Espacenet (EPO)', 'url': 'https://worldwide.espacenet.com/'},
        ],
        'limitations': [
            'These citations are a demonstration dataset and must be confirmed against actual patent registries before reliance.',
            'Synonyms are search aids; verify exact botanical identity (genus, species, variety) and claimed composition.',
            'A prior art match is not a patentability opinion, freedom-to-operate clearance, or infringement assessment.',
            'Similarity scores are illustrative and do not represent actual claim-by-claim comparison.',
            'Restricted databases (TKDL full-text, commercial patent databases) require authorised access and formal search review.',
            'For definitive prior art searches, engage a registered patent agent or use IP India / WIPO official search services.',
        ],
    }

class FeedbackInput(BaseModel):
    trace_id:str
    rating:int=Field(ge=1,le=5)
    reason:Literal['helpful','citation','unclear','missing','translation']

@app.post(PREFIX+'/feedback')
def feedback(body:FeedbackInput,session:Session=Depends(current_session),db:DBSession=Depends(get_db)):
    trace=db.get(AnswerTrace,body.trace_id)
    if not trace or trace.session_id!=session.id:raise HTTPException(404,'Answer not found.')
    db.add(Feedback(**body.model_dump()));db.commit();return {'ok':True}

@app.get(PREFIX+'/account/export')
def export_account(user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    return {'email':user.email,'cases':[case_dict(c) for c in db.scalars(select(Case).where(Case.user_id==user.id))],
        'consents':list_consents(user,db),'reviews':reviews(user,db)}

@app.delete(PREFIX+'/account')
def delete_account(response:Response,user:User=Depends(current_user),db:DBSession=Depends(get_db)):
    for case in db.scalars(select(Case).where(Case.user_id==user.id)):remove_case(db,case)
    db.execute(update(AuditEvent).where(AuditEvent.actor_id==user.id).values(actor_id=None))
    db.delete(user);db.commit();response.delete_cookie('ipsakti_session');return {'ok':True,'backup_note':'Deleted live data ages out of encrypted backups according to the documented backup retention policy.'}

@app.get(PREFIX+'/admin/jobs')
def jobs(user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    return [{'id':j.id,'kind':j.kind,'status':j.status,'payload':j.payload,'result':j.result,'attempts':j.attempts} for j in db.scalars(select(Job).order_by(Job.created_at.desc()).limit(100))]

class JobInput(BaseModel):
    kind:Literal['ingest','embed','purge']
    source_id:str|None=None
    ocr:bool=False

@app.post(PREFIX+'/admin/jobs',status_code=201)
def create_job(body:JobInput,user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    if body.kind=='ingest' and not db.get(Source,body.source_id):raise HTTPException(404,'Source not found in manifest.')
    job=Job(kind=body.kind,payload={'source_id':body.source_id,'ocr':body.ocr});db.add(job);db.flush();audit(db,'job.created',user.id,job.id);db.commit();return {'id':job.id}

class SourceReview(BaseModel):
    status:Literal['approved','reference_only','rejected']
    note:str=Field(min_length=30,max_length=3000)
    effective_from:str|None=Field(default=None,pattern=r'^\d{4}-\d{2}-\d{2}$')
    effective_to:str|None=Field(default=None,pattern=r'^\d{4}-\d{2}-\d{2}$')

@app.patch(PREFIX+'/admin/versions/{version_id}')
def review_source(version_id:str,body:SourceReview,user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    version=db.get(SourceVersion,version_id)
    if not version:raise HTTPException(404,'Version not found.')
    source=db.get(Source,version.source_id)
    if body.status=='approved' and source.authority in ('draft','notice','statistics','form'):raise HTTPException(422,'This document class cannot be promoted to governing answer authority.')
    if body.status=='approved' and version.quality.get('requires_review') and 'ocr' not in body.note.lower():raise HTTPException(422,'Record how OCR/extraction issues were resolved in the review note.')
    version.review_status=body.status;version.review_note=body.note;version.reviewer_id=user.id
    version.effective_from=body.effective_from;version.effective_to=body.effective_to
    audit(db,'source.reviewed',user.id,version.id,status=body.status);db.commit();return {'ok':True}

class ReleaseInput(BaseModel):
    name:str=Field(min_length=3,max_length=100)
    version_ids:list[str]=Field(min_length=1,max_length=500)
    review_note:str=Field(min_length=30,max_length=2000)

@app.get(PREFIX+'/admin/releases')
def releases(user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    return [{'id':r.id,'name':r.name,'active':r.active,'version_ids':r.version_ids,'review_note':r.review_note} for r in db.scalars(select(CorpusRelease).order_by(CorpusRelease.created_at.desc()))]

@app.post(PREFIX+'/admin/releases',status_code=201)
def create_release(body:ReleaseInput,user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    versions=db.scalars(select(SourceVersion).where(SourceVersion.id.in_(body.version_ids))).all()
    if len(versions)!=len(set(body.version_ids)) or any(v.review_status not in ('approved','reference_only') for v in versions):raise HTTPException(422,'All versions must have completed review.')
    if len({v.source_id for v in versions})!=len(versions):raise HTTPException(422,'A release may contain only one version of each source.')
    release=CorpusRelease(name=body.name,version_ids=body.version_ids,review_note=body.review_note);db.add(release);db.flush();audit(db,'release.created',user.id,release.id);db.commit();return {'id':release.id}

@app.post(PREFIX+'/admin/releases/{release_id}/activate')
def activate_release(release_id:str,user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    release=db.get(CorpusRelease,release_id)
    if not release:raise HTTPException(404,'Release not found.')
    versions=db.scalars(select(SourceVersion).where(SourceVersion.id.in_(release.version_ids))).all()
    if len(versions)!=len(release.version_ids) or any(v.review_status not in ('approved','reference_only') for v in versions):raise HTTPException(409,'Release includes unavailable or unreviewed versions.')
    db.execute(update(CorpusRelease).where(CorpusRelease.active==True).values(active=False));db.flush()
    release.active=True;audit(db,'release.activated',user.id,release.id);db.commit();return {'ok':True}

@app.get(PREFIX+'/graph')
def graph(db:DBSession=Depends(get_db)):
    release=active_release(db)
    if not release:return []
    return [{'id':e.id,'subject':e.subject,'predicate':e.predicate,'object':e.object,'evidence_chunk_id':e.evidence_chunk_id,'reviewed':e.reviewed} for e in db.scalars(select(GraphEdge).join(Chunk).where(GraphEdge.reviewed==True,Chunk.version_id.in_(release.version_ids)).limit(200))]

class EdgeInput(BaseModel):
    subject:str=Field(min_length=2,max_length=200)
    predicate:Literal['defines','requires','administered_by','amends','references','applies_to']
    object:str=Field(min_length=2,max_length=200)
    evidence_chunk_id:str
    reviewed:bool=False

@app.post(PREFIX+'/admin/graph',status_code=201)
def add_edge(body:EdgeInput,user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    chunk=db.get(Chunk,body.evidence_chunk_id)
    if not chunk:raise HTTPException(404,'Evidence excerpt not found.')
    edge=GraphEdge(**body.model_dump());db.add(edge);db.flush();audit(db,'graph.created',user.id,edge.id);db.commit();return {'id':edge.id}

@app.get(PREFIX+'/admin/audit')
def audit_events(user:User=Depends(roles('admin')),db:DBSession=Depends(get_db)):
    return [{'id':e.id,'action':e.action,'actor_id':e.actor_id,'resource_id':e.resource_id,'details':e.details,'created_at':e.created_at.isoformat()} for e in db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100))]

@app.get(PREFIX+'/admin/evaluations')
def evaluations(user:User=Depends(roles('curator','admin')),db:DBSession=Depends(get_db)):
    return [{'id':r.id,'dataset_version':r.dataset_version,'report':r.report} for r in db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(10))]
