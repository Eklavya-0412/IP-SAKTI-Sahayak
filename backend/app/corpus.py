"""Allowlisted acquisition, immutable snapshots and explicit corpus review.

Ingestion pipeline (PDF → Markdown → structured chunks):
  1. LlamaParse          — converts PDF to structured Markdown via cloud API
  2. MarkdownHeaderTextSplitter — splits on #/##/### headers, preserving metadata
  3. RecursiveCharacterTextSplitter — ensures no clause exceeds chunk_size chars
"""
import hashlib
import ipaddress
import json
import re
import socket
from pathlib import Path
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, text as sql
from .config import ROOT, settings
from .models import Source, SourceVersion, Chunk, CorpusRelease, now

MAX_DOWNLOAD = 35 * 1024 * 1024

ALLOWED_HOSTS = {
    'www.wipo.int', 'wipo.int', 'www.wto.org', 'wto.org', 'www.cbd.int', 'cbd.int',
    'absch.cbd.int', 'indiacode.nic.in', 'www.indiacode.nic.in', 'ipindia.gov.in',
    'www.ipindia.gov.in', 'cdsco.gov.in', 'fssai.gov.in', 'www.fssai.gov.in',
    'nbaindia.org', 'www.nbaindia.org', 'nbaindia.nic.in', 'www.nbaindia.nic.in',
    'plantauthority.gov.in', 'www.plantauthority.gov.in', 'www.meity.gov.in',
    'meity.gov.in', 'www.fda.gov', 'www.ema.europa.eu', 'www.gov.uk',
    'www.legislation.gov.uk', 'eur-lex.europa.eu', 'pcimh.gov.in', 'www.pcimh.gov.in',
    'ayush.gov.in', 'www.tkdl.res.in', 'tkdl.res.in', 'api.sci.gov.in',
    'main.sci.gov.in', 'www.nist.gov', 'genai.owasp.org',
    'upload.indiacode.nic.in', 'parivesh.nic.in', 'egazette.gov.in',
}

# ── URL safety ────────────────────────────────────────────────────────────────

def safe_url(url):
    parsed = urlparse(url)
    if (
        parsed.scheme != 'https'
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.port not in (None, 443)
        or parsed.username
    ):
        raise ValueError('Source URL is outside the HTTPS publisher allowlist.')
    for item in socket.getaddrinfo(parsed.hostname, 443):
        if not ipaddress.ip_address(item[4][0]).is_global:
            raise ValueError('Publisher resolved to a non-public address.')

# ── Download ──────────────────────────────────────────────────────────────────

def download(url):
    with httpx.Client(
        timeout=45,
        follow_redirects=False,
        headers={'User-Agent': 'IP-SAKTI-ResearchPilot/1.0 (source preservation; low volume)'},
    ) as client:
        for _ in range(5):
            safe_url(url)
            with client.stream('GET', url) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers['location'])
                    continue
                response.raise_for_status()
                body = bytearray()
                for part in response.iter_bytes():
                    body.extend(part)
                    if len(body) > MAX_DOWNLOAD:
                        raise ValueError('Source exceeds download limit.')
                return bytes(body), response.headers.get('content-type', ''), url
    raise ValueError('Too many source redirects.')

# ── LlamaParse extraction ─────────────────────────────────────────────────────

def extract_with_llamaparse(path: Path) -> tuple[str, dict]:
    """
    Parse a PDF using LlamaParse and return (markdown_text, quality_metadata).

    LlamaParse handles:
    - Scanned / image PDFs (built-in OCR)
    - Multi-column layouts
    - Tables and footnotes
    - Devanagari / multilingual text

    Requires LLAMA_CLOUD_API_KEY in .env.
    """
    cfg = settings()
    if not cfg.llama_cloud_api_key:
        raise ValueError(
            'LLAMA_CLOUD_API_KEY is not set. '
            'Get a free key at https://cloud.llamaindex.ai and add it to .env.'
        )
    try:
        from llama_parse import LlamaParse  # type: ignore
    except ImportError:
        raise RuntimeError(
            'llama-parse is not installed. Run: pip install llama-parse'
        )

    parser = LlamaParse(
        api_key=cfg.llama_cloud_api_key,
        result_type=cfg.llama_parse_result_type,   # 'markdown'
        verbose=False,
        language='en',                              # LlamaParse auto-detects Hindi/Marathi
        skip_diagonal_text=True,
        do_not_unroll_columns=False,
    )
    documents = parser.load_data(str(path))
    if not documents:
        raise ValueError('LlamaParse returned no content for this file.')

    full_markdown = '\n\n'.join(doc.text for doc in documents)
    quality = {
        'pages': len(documents),
        'method': 'llamaparse',
        'result_type': cfg.llama_parse_result_type,
        'requires_review': True,     # always requires expert sign-off
        'expert_reviewed': False,
        'ocr_pages': [],
        'sparse_pages': [],
    }
    return full_markdown, quality


def extract_html(path: Path) -> tuple[str, dict]:
    """Extract plain text from HTML, stripping chrome elements."""
    soup = BeautifulSoup(path.read_bytes(), 'html.parser')
    for node in soup(['script', 'style', 'nav', 'header', 'footer', 'form', 'noscript']):
        node.decompose()
    main = soup.find('main') or soup.find('article') or soup.body or soup
    text = main.get_text('\n', strip=True)
    quality = {
        'pages': 1,
        'method': 'bs4',
        'requires_review': True,
        'expert_reviewed': False,
    }
    return text, quality


# ── Chunking pipeline ─────────────────────────────────────────────────────────

# Markdown headers used for semantic splitting.
# Level 1 → Chapter, Level 2 → Section, Level 3 → Sub-section.
HEADER_SPLITS = [
    ('#',   'chapter'),
    ('##',  'section'),
    ('###', 'subsection'),
]


def split_markdown(markdown_text: str) -> list[dict]:
    """
    Split Markdown produced by LlamaParse into structured chunks.

    Pipeline:
      MarkdownHeaderTextSplitter  →  header-aware documents
      RecursiveCharacterTextSplitter  →  enforce chunk_size / chunk_overlap

    Each yielded dict has the keys expected by Chunk:
      ordinal, heading, locator, page, start_offset, end_offset, text
    """
    from langchain_text_splitters import (
        MarkdownHeaderTextSplitter,
        RecursiveCharacterTextSplitter,
    )
    cfg = settings()

    # Step 1 — split on Markdown headers, keeping header metadata attached
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADER_SPLITS,
        strip_headers=False,        # keep the header line in chunk text
        return_each_line=False,
    )
    header_docs = header_splitter.split_text(markdown_text)

    # Step 2 — fine-grain split to respect chunk_size, preserving legal sentences
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,          # default 1500
        chunk_overlap=cfg.chunk_overlap,    # default 200
        separators=[
            '\n\n',     # paragraph break (highest priority)
            '\n',       # line break
            '। ',       # Devanagari sentence end
            '. ',       # English sentence end
            '; ',       # clause separator
            ', ',       # sub-clause
            ' ',        # word boundary (last resort)
            '',
        ],
        length_function=len,
        is_separator_regex=False,
        keep_separator=True,
    )

    chunks = []
    ordinal = 0
    for header_doc in header_docs:
        meta = header_doc.metadata   # e.g. {'chapter': 'Chapter 1', 'section': 'Section 2'}

        # Build a human-readable heading from all header levels present
        heading_parts = [
            meta[level]
            for _, level in HEADER_SPLITS
            if meta.get(level)
        ]
        heading = ' > '.join(heading_parts)[:300] or 'Preamble'

        # Fine-grained split
        sub_docs = char_splitter.split_documents([header_doc])
        for sub in sub_docs:
            text = sub.page_content.strip()
            if len(text) < 60:          # discard noise fragments
                continue
            chunks.append(dict(
                ordinal=ordinal,
                heading=heading,
                locator=heading,
                page=None,              # LlamaParse flattens to Markdown; no page number
                start_offset=0,         # offsets are not meaningful post-splitter
                end_offset=len(text),
                text=text,
            ))
            ordinal += 1

    return chunks


def split_plain_text(text: str) -> list[dict]:
    """
    Fallback splitter for HTML / plain-text sources (no Markdown headers).
    Uses RecursiveCharacterTextSplitter only.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    cfg = settings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        separators=['\n\n', '\n', '। ', '. ', '; ', ', ', ' ', ''],
        length_function=len,
        keep_separator=True,
    )
    raw_chunks = splitter.split_text(text)
    chunks = []
    ordinal = 0
    for raw in raw_chunks:
        stripped = raw.strip()
        if len(stripped) < 60:
            continue
        chunks.append(dict(
            ordinal=ordinal,
            heading='',
            locator='Official page excerpt',
            page=None,
            start_offset=0,
            end_offset=len(stripped),
            text=stripped,
        ))
        ordinal += 1
    return chunks

# ── Manifest loading ──────────────────────────────────────────────────────────

def load_manifest(db):
    path = settings().corpus_manifest
    if not path.is_file():
        # Manifest is missing (e.g. running tests without the corpus directory,
        # or the CORPUS_MANIFEST env var points to a Docker path).
        # Return a no-op empty manifest instead of crashing.
        return {'sources': []}
    manifest = json.loads(path.read_text(encoding='utf-8'))
    for entry in manifest['sources']:
        source = db.get(Source, entry['id'])
        values = {
            k: entry[k]
            for k in ('title', 'publisher', 'url', 'jurisdiction', 'market',
                      'language', 'authority', 'category', 'access', 'notes')
            if k in entry
        }
        if not source:
            db.add(Source(id=entry['id'], disposition=entry.get('disposition', 'pending'), **values))
        else:
            for k, v in values.items():
                setattr(source, k, v)
    db.commit()
    return manifest

# ── Ingest ────────────────────────────────────────────────────────────────────

def ingest(db, entry, use_ocr=False):  # use_ocr kept for API compat; handled by LlamaParse
    source = db.get(Source, entry['id'])
    if entry.get('disposition') in ('excluded', 'pointer', 'background'):
        return {'status': 'skipped', 'reason': entry.get('notes')}

    if entry.get('local_path'):
        origin = (ROOT / entry['local_path']).resolve()
        if not origin.is_relative_to((ROOT / 'Resources').resolve()):
            raise ValueError('Local source must be in Resources.')
        body = origin.read_bytes()
        ext = origin.suffix.lower()
        resolved_url = entry['url']
    else:
        body, content_type, resolved_url = download(entry['url'])
        ext = '.pdf' if body.startswith(b'%PDF') else '.html'

    checksum = hashlib.sha256(body).hexdigest()
    source.checked_at = now()

    existing = db.scalar(
        select(SourceVersion).where(
            SourceVersion.source_id == source.id,
            SourceVersion.checksum == checksum,
        )
    )
    if existing:
        db.commit()
        return {'status': 'unchanged', 'version_id': existing.id}

    # Persist raw snapshot
    folder = settings().storage_dir / 'snapshots' / source.id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{checksum}{ext}'
    if not path.exists():
        path.write_bytes(body)

    # Extract and chunk
    if ext == '.pdf':
        content, quality = extract_with_llamaparse(path)
        chunk_dicts = split_markdown(content)
    else:
        content, quality = extract_html(path)
        chunk_dicts = split_plain_text(content)

    quality['resolved_url'] = resolved_url
    quality['source_origin'] = 'user_supplied' if entry.get('local_path') else 'official_download'

    version = SourceVersion(
        source_id=source.id,
        checksum=checksum,
        path=str(path),
        quality=quality,
        effective_from=entry.get('effective_from'),
        publication_date=entry.get('publication_date'),
        review_status='pending',
        review_note='Awaiting extraction, applicability and provenance review.',
    )
    db.add(version)
    db.flush()

    chunks = [Chunk(version_id=version.id, **data) for data in chunk_dicts]
    db.add_all(chunks)
    source.disposition = 'review_required'
    db.commit()

    return {
        'status': 'ingested',
        'version_id': version.id,
        'chunks': len(chunks),
        'quality': quality,
    }

# ── Re-parse (replaces reprocess_ocr) ────────────────────────────────────────

def reparse_with_llamaparse(db, source_id):
    """
    Re-run LlamaParse on the stored snapshot for a source.

    Replaces the old Tesseract-based reprocess_ocr(). LlamaParse handles OCR
    natively for scanned/image PDFs. New chunks are appended without modifying
    already-cited chunk identifiers.
    """
    from sqlalchemy import func
    version = db.scalar(
        select(SourceVersion)
        .where(SourceVersion.source_id == source_id)
        .order_by(SourceVersion.retrieved_at.desc())
    )
    if not version:
        raise ValueError('Acquire the source first.')
    if version.review_status == 'approved':
        raise ValueError(
            'Approved extraction cannot be changed; use a curator-managed new release.'
        )

    path = Path(version.path)
    if not path.exists():
        raise ValueError(f'Snapshot file not found: {path}')

    # Full re-parse — produces a new complete chunk set
    markdown_text, quality_update = extract_with_llamaparse(path)
    new_chunks = split_markdown(markdown_text)

    # Ordinal continues from the highest existing ordinal
    max_ordinal = db.scalar(
        select(func.max(Chunk.ordinal)).where(Chunk.version_id == version.id)
    ) or 0
    total = 0
    for data in new_chunks:
        data['ordinal'] = max_ordinal + data['ordinal'] + 1
        data['locator'] = 'LlamaParse re-parse · ' + (data['locator'] or '')
        db.add(Chunk(version_id=version.id, **data))
        total += 1

    updated_quality = {**version.quality, **quality_update, 'requires_review': True}
    version.quality = updated_quality
    db.commit()

    return {'reparsed_chunks': total, 'expert_reviewed': False}

# ── Corpus release management ─────────────────────────────────────────────────

def reference_release(db, name='Supplied reference library'):
    """Activate searchable references — explicitly NOT a legally approved release."""
    versions = db.scalars(
        select(SourceVersion)
        .join(Source)
        .where(
            Source.authority.notin_(['draft', 'statistics', 'notice']),
            SourceVersion.review_status == 'pending',
        )
    ).all()
    ids = []
    for v in versions:
        if db.scalar(select(Chunk.id).where(Chunk.version_id == v.id).limit(1)):
            v.review_status = 'reference_only'
            v.review_note = (
                'Extraction available for source discovery. '
                'Legal applicability and expert review remain pending.'
            )
            ids.append(v.id)

    old = db.scalar(select(CorpusRelease).where(CorpusRelease.active == True))
    if old:
        old.active = False
        ids = list(set(old.version_ids + ids))

    # Keep exactly one snapshot per source
    candidates = db.scalars(
        select(SourceVersion)
        .where(SourceVersion.id.in_(ids))
        .order_by(SourceVersion.retrieved_at.desc())
    ).all()
    latest = {}
    for version in candidates:
        latest.setdefault(version.source_id, version.id)
    ids = list(latest.values())
    db.flush()

    release = CorpusRelease(
        name=name,
        version_ids=ids,
        active=True,
        review_note='Reference-only baseline. No expert sign-off claimed.',
    )
    db.add(release)
    db.commit()
    return release


def active_release(db):
    return db.scalar(select(CorpusRelease).where(CorpusRelease.active == True))

# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_chunks(db):
    from .retrieval import encoder
    model = encoder()
    if model is None:
        raise ValueError('Enable embeddings and pin a model revision first.')
    total = 0
    while True:
        rows = db.scalars(select(Chunk).where(Chunk.embedding.is_(None)).limit(32)).all()
        if not rows:
            break
        vectors = model.encode(
            ['passage: ' + c.heading + ' ' + c.text for c in rows],
            normalize_embeddings=True,
        ).tolist()
        for chunk, vector in zip(rows, vectors):
            chunk.embedding = vector
            db.execute(
                sql('UPDATE chunks SET vector_embedding=CAST(:v AS vector) WHERE id=:id'),
                {'v': json.dumps(vector), 'id': chunk.id},
            )
        db.commit()
        total += len(rows)
    return total
