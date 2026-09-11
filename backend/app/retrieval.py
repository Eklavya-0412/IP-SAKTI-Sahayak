import json
import math
import re
from collections import Counter
from datetime import date, timedelta
from functools import lru_cache
from sqlalchemy import select, text as sql
from .models import Chunk, Source, SourceVersion, GraphEdge, now
from .config import settings
from .corpus import active_release
from .schemas import Citation

# A deterministic glossary improves lexical access without sending a query to a third party.
GLOSSARY = {
 'पेटेंट':'patent', 'पेटेन्ट':'patent', 'पेटंट':'patent', 'पारंपरिक':'traditional', 'ज्ञान':'knowledge',
 'औषधि':'drug medicine', 'औषध':'drug medicine', 'आयुर्वेद':'ayurveda ayurvedic', 'आयुर्वेदिक':'ayurvedic',
 'आहार':'aahara food', 'भोजन':'food', 'अन्न':'food', 'जैविक':'biological', 'जैवविविधता':'biodiversity',
 'जैव':'biological', 'लाभ':'benefit', 'वाटप':'sharing', 'साझाकरण':'sharing', 'साझेदारी':'sharing',
 'ट्रेडमार्क':'trademark', 'व्यापार':'trade', 'चिह्न':'mark', 'भौगोलिक':'geographical', 'संकेत':'indication',
 'कॉपीराइट':'copyright', 'प्रतिलिप्यधिकार':'copyright', 'डिजाइन':'design', 'डिझाइन':'design',
 'पौधा':'plant', 'वनस्पती':'plant', 'किस्म':'variety', 'वाण':'variety', 'सूक्ष्मजीव':'microorganism',
 'निर्यात':'export', 'विज्ञापन':'advertising', 'जाहिरात':'advertising', 'लेबल':'labelling',
 'सुरक्षा':'safety', 'प्रभावकारिता':'efficacy', 'परवाना':'licence', 'लाइसेंस':'licence', 'शास्त्रीय':'classical',
 'अमेरिका':'US FDA', 'यूरोप':'EU herbal', 'युरोप':'EU herbal', 'नागोया':'nagoya', 'पारिस्थितिक':'biodiversity',
 'गोष्ट':'', 'नियम':'rules', 'कानून':'act law', 'कायदा':'act law', 'संरक्षण':'protection',
}
STOP = set('what is are a an the of in on for and or to i my can how does do with from under about me tell please should which when this that it as be'.split())

def normalize_query(value):
    extra = [english for term,english in GLOSSARY.items() if term in value]
    return value + ' ' + ' '.join(extra)

def tokens(value):
    canonical={'patented':'patent','patents':'patent','patenting':'patent','patentable':'patent','patentability':'patent',
      'formulations':'formulation','medicines':'medicine','drugs':'drug','resources':'resource','rights':'right',
      'inventions':'invention','varieties':'variety','ingredients':'ingredient','regulations':'regulation','rules':'rule',
      'requirements':'requirement','trademarks':'trademark','designs':'design','exemptions':'exemption'}
    return [canonical.get(t,t) for t in re.findall(r'[^\W_]+',value.lower(),re.UNICODE) if len(t)>1 and t not in STOP]

@lru_cache(maxsize=20000)
def term_counts(text):
    # Cache immutable public text only, never questions or private documents.
    return Counter(tokens(text))

@lru_cache(maxsize=1)
def encoder():
    cfg=settings()
    if not cfg.embeddings_enabled or not cfg.embedding_revision: return None
    from sentence_transformers import SentenceTransformer
    snapshot=cfg.storage_dir/'models'/('models--'+cfg.embedding_model.replace('/','--'))/'snapshots'/cfg.embedding_revision
    local=snapshot.is_dir() and (snapshot/'config.json').exists()
    return SentenceTransformer(str(snapshot) if local else cfg.embedding_model,revision=None if local else cfg.embedding_revision,
        device='cpu',cache_folder=str(cfg.storage_dir/'models'),trust_remote_code=False,local_files_only=local)

def eligible_rows(db, jurisdiction, market, as_of=None, approved_only=False):
    release=active_release(db)
    if not release or not release.version_ids: return []
    allowed=['approved'] if approved_only else ['approved','reference_only']
    statement=(select(Chunk,SourceVersion,Source).join(SourceVersion,Chunk.version_id==SourceVersion.id)
        .join(Source,SourceVersion.source_id==Source.id)
        .where(SourceVersion.id.in_(release.version_ids),SourceVersion.review_status.in_(allowed),
               Source.jurisdiction==jurisdiction,Source.market==market,Source.authority.notin_(['draft','statistics','notice','private','form'])))
    target=as_of or date.today().isoformat()
    return [r for r in db.execute(statement).all()
            if (not r[1].effective_from or r[1].effective_from<=target) and (not r[1].effective_to or target<r[1].effective_to)]

def retrieve(db, query, jurisdiction, market='treaties', as_of=None, limit=8, approved_only=False, category=None):
    rows=eligible_rows(db,jurisdiction,market,as_of,approved_only)
    if category: rows=[r for r in rows if r[2].category==category]
    if not rows: return [], {'retrieval':'empty','candidates':0}
    terms=tokens(normalize_query(query))
    if not terms: return [], {'retrieval':'empty','candidates':0}
    counts=[term_counts(c.heading+' '+c.text) for c,_,_ in rows]
    df=Counter(t for t in set(terms) for count in counts if t in count)
    avg=sum(sum(c.values()) for c in counts)/len(counts) or 1
    lexical=[]
    preferred=set()
    regulatory_question=bool(re.search(r'proprietary|classif|dosage form|authoritative text',query,re.I))
    for term,category_name in [('patent','patents'),('trademark','trademarks'),('copyright','copyright'),('design','designs'),
      ('biodiversity','abs'),('abs','abs'),('aahara','aahara'),('variety','plant_varieties'),('geographical','gi')]:
        if term in terms and not (term=='patent' and regulatory_question): preferred.add(category_name)
    if regulatory_question:
        preferred.add('classification')
    for idx,count in enumerate(counts):
        length=sum(count.values())
        score=sum(math.log(1+(len(rows)-df[t]+.5)/(df[t]+.5)) * (count[t]*2.2)/(count[t]+1.2*(.25+.75*length/avg)) for t in set(terms) if count[t])
        if rows[idx][2].category in preferred: score*=2.5
        if score>0: lexical.append((idx,score))
    lexical.sort(key=lambda x:x[1],reverse=True)
    # PostgreSQL's indexed full-text query augments the portable BM25 ranking.
    if db.bind.dialect.name=='postgresql':
        ids=[r[0].id for r in rows]
        result=db.execute(sql("SELECT id FROM chunks WHERE id = ANY(:ids) AND search_vector @@ plainto_tsquery('simple', :q) ORDER BY ts_rank_cd(search_vector, plainto_tsquery('simple', :q)) DESC LIMIT 30"),{'ids':ids,'q':' '.join(terms)}).scalars().all()
        positions={r[0].id:i for i,r in enumerate(rows)}
        sql_order=[(positions[i],100.) for i in result]
        seen={i for i,_ in sql_order}
        lexical=sql_order+[x for x in lexical if x[0] not in seen]
    ranks={idx:1/(60+rank) for rank,(idx,_) in enumerate(lexical[:30],1)}
    dense=[]
    embedding_error=None
    try: model=encoder()
    except Exception as error:
        model=None;embedding_error=type(error).__name__
    if model:
        vector=model.encode(['query: '+normalize_query(query)],normalize_embeddings=True)[0].tolist()
        if db.bind.dialect.name=='postgresql':
            ids=[r[0].id for r in rows]
            order=db.execute(sql('SELECT id, 1-(vector_embedding <=> CAST(:v AS vector)) AS similarity FROM chunks WHERE id=ANY(:ids) AND vector_embedding IS NOT NULL ORDER BY vector_embedding <=> CAST(:v AS vector) LIMIT 30'),{'v':json.dumps(vector),'ids':ids}).all()
            positions={r[0].id:i for i,r in enumerate(rows)}
            dense=[(positions[i],sim) for i,sim in order if sim>.65]
        else:
            dense=sorted([(i,sum(a*b for a,b in zip(vector,r[0].embedding))) for i,r in enumerate(rows) if r[0].embedding],key=lambda x:x[1],reverse=True)[:30]
            dense=[p for p in dense if p[1]>.65]
        for rank,(idx,_) in enumerate(dense,1): ranks[idx]=ranks.get(idx,0)+1/(60+rank)
    ordered=sorted(ranks,key=ranks.get,reverse=True)
    # Do not fill results with unrelated pages sharing a single incidental term.
    result=[]
    for idx in ordered:
        overlap=len(set(terms)&set(counts[idx]))
        if overlap < min(2,len(set(terms))) and idx not in {i for i,_ in dense}: continue
        result.append(rows[idx])
        if len(result)>=limit: break
    return result, {'retrieval':'hybrid' if dense else 'lexical','candidates':len(rows),'matched':len(result),'embeddings_enabled':model is not None,'embedding_error':embedding_error}

def local_query_plan(queries, jurisdiction):
    """Expand botanical patent questions into independent evidence topics.

    These are search terms, not legal conclusions. Scope filters still apply to
    every search and to graph expansion, including on cyclic retries.
    """
    planned=list(dict.fromkeys(queries))
    # Respect an existing multi-query plan; expand only an unplanned question.
    context=queries[0].lower() if len(queries)==1 else ''
    if jurisdiction=='india' and re.search(r'patent|पेटेंट|पेटंट',context) and re.search(r'ayurved|ayush|herbal|botanical|formulation|आयुर्वेद',context):
        planned.extend([
            'traditional knowledge invention aggregation duplication known properties Section 3(p)',
            'biological resources intellectual property invention National Biodiversity Authority approval registration',
        ])
    return list(dict.fromkeys(planned))[:4]


def retrieve_queries(db, queries, jurisdiction, market='treaties', as_of=None, limit=8):
    """Fuse independent semantic searches, then diversify document evidence."""
    scores={}; candidates={}; runs=[]
    for query in local_query_plan(queries,jurisdiction):
        rows,metrics=retrieve(db,query,jurisdiction,market,as_of,limit=12)
        runs.append(metrics)
        for rank,row in enumerate(rows,1):
            key=row[0].id
            scores[key]=scores.get(key,0)+1/(60+rank)
            candidates[key]=row
    ordered=sorted(scores,key=scores.get,reverse=True)
    chosen=[]; per_source=Counter(); selected=set()
    # Cover distinct relevant documents before spending slots on more pages of
    # the same manual. Otherwise repeated guidance can crowd out the statute.
    for cap in (1, 2, 3):
        for key in ordered:
            row=candidates[key]
            if key in selected or per_source[row[2].id]>=cap: continue
            chosen.append(row); selected.add(key); per_source[row[2].id]+=1
            if len(chosen)>=limit:break
        if len(chosen)>=limit:break
    return chosen,{'retrieval':'hybrid' if any(r.get('retrieval')=='hybrid' for r in runs) else 'lexical',
                   'query_count':len(runs),'matched':len(chosen),'distinct_sources':len(per_source),
                   'embeddings_enabled':any(r.get('embeddings_enabled') for r in runs),
                   'embedding_error':next((r['embedding_error'] for r in runs if r.get('embedding_error')),None)}

def expand_graph(db, rows, jurisdiction, market, as_of=None):
    if not rows: return rows, []
    eligible={r[0].id:r for r in eligible_rows(db,jurisdiction,market,as_of)}
    ids={r[0].id for r in rows}
    edges=db.scalars(select(GraphEdge).where(GraphEdge.reviewed==True,GraphEdge.evidence_chunk_id.in_(ids)).limit(8)).all()
    entities={e.subject for e in edges}|{e.object for e in edges}
    related=db.scalars(select(GraphEdge).where(GraphEdge.reviewed==True,GraphEdge.subject.in_(entities)).limit(12)).all() if entities else []
    out=list(rows)
    for edge in related:
        if edge.evidence_chunk_id in eligible and edge.evidence_chunk_id not in ids:
            out.append(eligible[edge.evidence_chunk_id]); ids.add(edge.evidence_chunk_id)
        if len(out)>=10: break
    return out, [e.id for e in edges+related if e.evidence_chunk_id in ids]

def citation(row):
    chunk,version,source=row
    url=source.url
    if '.pdf' in url.lower() and chunk.page: url=url.split('#')[0]+f'#page={chunk.page}'
    return Citation(id=chunk.id,source_id=source.id,version_id=version.id,title=source.title,publisher=source.publisher,
        url=url,locator=chunk.locator,page=chunk.page,excerpt=chunk.text,authority=source.authority,
        jurisdiction=source.jurisdiction,market=source.market,retrieved_at=version.retrieved_at.isoformat(),
        review_status=version.review_status,stale=source.checked_at is None or source.checked_at<now()-timedelta(days=settings().source_stale_days))
