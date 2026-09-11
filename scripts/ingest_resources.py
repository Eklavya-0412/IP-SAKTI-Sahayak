"""Ingest manifest-mapped PDFs as page-aware reference evidence.

Run from any directory. --extract-only performs PDF QA without a database/model.
The default uses pypdf locally. No expert approval or effective dates are invented.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'scripts'))
MODEL = 'intfloat/multilingual-e5-small'
REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'


def ocr_page(page):
    import tempfile
    from pypdf import PdfWriter
    from app.config import settings
    with tempfile.TemporaryDirectory(prefix='ipsakti-ocr-') as folder:
        path = Path(folder)/'page.pdf'
        writer=PdfWriter()
        writer.add_page(page)
        writer.write(path)
        cache=ROOT/'data'/'extractions'/(hashlib.sha256(path.read_bytes()).hexdigest()+'.md')
        if cache.exists():
            return cache.read_text(encoding='utf-8')
        if not settings().llama_cloud_api_key:
            raise ValueError('Scanned PDF page requires LLAMA_CLOUD_API_KEY for page-preserving OCR.')
        from llama_parse import LlamaParse
        documents=LlamaParse(api_key=settings().llama_cloud_api_key,result_type='markdown',verbose=False).load_data(str(path))
        content='\n\n'.join(document.text for document in documents)
        if content.strip():
            cache.parent.mkdir(parents=True,exist_ok=True)
            cache.write_text(content,encoding='utf-8')
        return content


def extract_document(path, title):
    from pypdf import PdfReader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200, add_start_index=True)
    reader = PdfReader(path)
    chunks, sparse, ocr_pages = [], [], []
    for page_number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        if len(text.strip()) < 40:
            sparse.append(page_number)
            # Blank separator pages have no images; scanned pages require OCR.
            if page.images:
                print(f'OCR {path.name}: page {page_number}',flush=True)
                extracted = ocr_page(page)
                if not extracted.strip():
                    raise ValueError(f'OCR returned no text: {path.name}, page {page_number}')
                text = extracted
                ocr_pages.append(page_number)
        heading = next((line.strip() for line in text.splitlines() if len(line.strip()) > 8), title)[:300]
        for document in splitter.create_documents([text]):
            content = document.page_content
            if not content.strip():
                continue
            offset = document.metadata['start_index']
            if offset < 0 or text[offset:offset+len(content)] != content:
                raise ValueError(f'Unverifiable chunk offsets in {path.name}, page {page_number}')
            chunks.append(dict(ordinal=len(chunks), heading=heading, locator=f'Page {page_number}',
                page=page_number, start_offset=offset, end_offset=offset+len(content), text=content))
    if not chunks:
        raise ValueError(f'No extractable text: {path.name}. OCR is required before ingestion.')
    return chunks, {'method':'pypdf+llamaparse' if ocr_pages else 'pypdf', 'pages':len(reader.pages), 'sparse_pages':sparse, 'ocr_pages':ocr_pages,
        'requires_review':True, 'expert_reviewed':False, 'embedding_model':MODEL,
        'embedding_revision':REVISION, 'chunk_size':1500, 'chunk_overlap':200}


def resources(manifest, directory):
    entries = [entry for entry in manifest['sources'] if entry.get('local_path')]
    mapped = {Path(entry['local_path']).name:entry for entry in entries}
    actual = {p.name for p in directory.glob('*.pdf')}
    missing, unknown = set(mapped)-actual, actual-set(mapped)
    if missing or unknown:
        raise ValueError(f'Resource/manifest mismatch: missing={sorted(missing)}, unmapped={sorted(unknown)}')
    if not mapped:
        raise ValueError('No local PDF resources mapped in the manifest')
    for filename, entry in mapped.items():
        yield entry, directory / filename


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=ROOT/'Resources')
    parser.add_argument('--manifest', type=Path, default=ROOT/'corpus/manifest.json')
    parser.add_argument('--extract-only', action='store_true')
    parser.add_argument('--report', type=Path, default=ROOT/'docs/ingestion-report.json')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    prepared, report = [], {'documents':[], 'mode':'extraction' if args.extract_only else 'live', 'status':'preparing', 'committed':False}
    # Validate the entire supplied library before touching the database.
    for entry, path in resources(manifest, args.resources):
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        cache=ROOT/'data'/'extractions'/(checksum+'-chunks-v1.json')
        if cache.exists():
            parsed=json.loads(cache.read_text(encoding='utf-8'))
            chunks,quality=parsed['chunks'],parsed['quality']
        else:
            chunks, quality = extract_document(path, entry['title'])
            cache.parent.mkdir(parents=True,exist_ok=True)
            cache.write_text(json.dumps({'chunks':chunks,'quality':quality},ensure_ascii=False),encoding='utf-8')
        prepared.append((entry, path, checksum, chunks, quality))
        report['documents'].append({'source_id':entry['id'],'file':path.name,'sha256':checksum,
            'chunks':len(chunks),'pages':quality['pages'],'sparse_pages':quality['sparse_pages'],'ocr_pages':quality['ocr_pages']})
        print(f'{path.name}: {quality["pages"]} pages, {len(chunks)} chunks', flush=True)
    report['chunks'] = sum(len(item[3]) for item in prepared)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    if args.extract_only:
        report['status']='extraction_complete'
        args.report.write_text(json.dumps(report,indent=2),encoding='utf-8')
        return

    from sqlalchemy import select, text, update
    from app.config import settings
    from app.db import SessionLocal, engine
    from app.models import Source, SourceVersion, Chunk, CorpusRelease
    from seed_graph import seed_graph
    if engine.dialect.name != 'postgresql':
        raise RuntimeError('Live ingestion requires PostgreSQL with pgvector; use --extract-only for PDF QA.')
    # Fail before downloading a model if the database or migrated vector column is unavailable.
    with engine.connect() as connection:
        connection.execute(text('SELECT vector_embedding FROM chunks LIMIT 0'))
    from sentence_transformers import SentenceTransformer
    cache_folder=settings().storage_dir/'models'
    snapshot=cache_folder/('models--'+MODEL.replace('/','--'))/'snapshots'/REVISION
    local=(snapshot/'config.json').exists() and any((snapshot/name).exists() for name in ('model.safetensors','pytorch_model.bin'))
    model = SentenceTransformer(str(snapshot) if local else MODEL, revision=None if local else REVISION, device='cpu',
        cache_folder=str(cache_folder), trust_remote_code=False,local_files_only=local)
    if model.get_sentence_embedding_dimension() != 384:
        raise ValueError('Expected 384-dimensional embeddings')
    version_ids = []
    with SessionLocal.begin() as db:
        # Serialize this importer and release activation in this transaction.
        db.execute(text('SELECT pg_advisory_xact_lock(26045003)'))
        for entry, path, checksum, chunks, quality in prepared:
            source = db.get(Source, entry['id'])
            if source is None:
                keys = ('title','publisher','url','jurisdiction','market','language','authority','category','access','notes')
                source = Source(id=entry['id'], **{k:entry[k] for k in keys if k in entry})
                db.add(source)
                db.flush()
            source.url=entry['url']
            source.publisher=entry['publisher']
            version = db.scalar(select(SourceVersion).where(SourceVersion.source_id==source.id, SourceVersion.checksum==checksum))
            if version and version.review_status in ('rejected','pending'):
                raise ValueError(f'{source.id} already has a {version.review_status} version; resolve its review explicitly first.')
            snapshot = settings().storage_dir/'snapshots'/source.id/(checksum+'.pdf')
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if not snapshot.exists():
                snapshot.write_bytes(path.read_bytes())
            if version is not None:
                version.path=str(snapshot.resolve())
            if version is None:
                version = SourceVersion(source_id=source.id, checksum=checksum, path=str(snapshot.resolve()),
                    review_status='reference_only', review_note='Supplied reference library. Local extraction only; no expert legal approval recorded.', quality=quality)
                db.add(version)
                db.flush()
            existing = db.scalars(select(Chunk).where(Chunk.version_id==version.id).order_by(Chunk.ordinal)).all()
            if existing:
                if len(existing)!=len(chunks) or any(c.text!=part['text'] or c.page!=part['page'] or c.heading!=part['heading'] for c,part in zip(existing,chunks)):
                    raise ValueError(f'{source.id}: existing chunk structure differs; refusing to invalidate citations.')
                rows = existing
            else:
                rows = [Chunk(version_id=version.id, **part) for part in chunks]
                db.add_all(rows)
                db.flush()
            # Recompute pinned embeddings on reruns to repair missing/incompatible vectors.
            for start in range(0,len(rows),64):
                batch = rows[start:start+64]
                vectors = model.encode(['passage: '+row.heading+' '+row.text for row in batch],
                    normalize_embeddings=True, batch_size=32, show_progress_bar=False).tolist()
                values = []
                for row, vector in zip(batch,vectors):
                    if len(vector)!=384 or not all(math.isfinite(x) for x in vector):
                        raise ValueError('Invalid embedding')
                    row.embedding=vector
                    values.append({'id':row.id,'vector':json.dumps(vector)})
                db.flush()
                db.execute(text('UPDATE chunks SET vector_embedding=CAST(:vector AS vector) WHERE id=:id'),values)
            version_ids.append(version.id)
            print(f'Embedded {source.id}: {len(rows)} chunks', flush=True)
        previous = db.scalar(select(CorpusRelease).where(CorpusRelease.active==True))
        # Retain other sources (e.g. FDA/NBA) already present in the active release.
        replaced = {entry['id'] for entry, *_ in prepared}
        retained = []
        if previous:
            retained = list(db.scalars(select(SourceVersion.id).where(SourceVersion.id.in_(previous.version_ids), SourceVersion.source_id.notin_(replaced))))
        target_ids = sorted(set(version_ids+retained))
        if previous and sorted(previous.version_ids)==target_ids:
            release=previous
        else:
            db.execute(update(CorpusRelease).where(CorpusRelease.active==True).values(active=False))
            db.flush()
            release=CorpusRelease(name='Supplied reference library',version_ids=target_ids,active=True,
                review_note='Page-aware reference ingestion. Expert approval is recorded separately per source version.')
            db.add(release)
            db.flush()
        edges=seed_graph(db,release)
        report.update(release_id=release.id,version_ids=version_ids,graph_edges_created=edges,active=True)
    report.update(status='committed',committed=True)
    args.report.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'release_id':report['release_id'],'chunks':report['chunks'],'active':True}))


if __name__ == '__main__':
    main()
