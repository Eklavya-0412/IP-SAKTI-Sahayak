"""
Multi-Agent LangGraph Orchestration for IP-SAKTI Sahayak.

Architecture (cyclic graph):

    START
      │
      ▼
  triage_agent ──(blocked)──► END
      │
      ▼ (clear)
  retrieve_agent ◄──────────────────────┐
      │                                 │ retry (expand terms)
      ▼                                 │
  compose_agent ──(low confidence)──────┘
      │
      ▼ (claims verified)
  translate_agent
      │
      ▼
     END

Key differences from the old linear graph:
- triage_agent: Uses Groq to classify intent and validate jurisdiction before retrieval.
  Blocks immediately (no LLM call wasted) if the query is unsafe/clinical/off-domain.
- retrieve_agent: Tracks retry_count. On the second pass it expands the query via
  LLM query-planning and broadens the jurisdiction filter to 'treaties'.
- compose_agent: If 0 verified claims come back AND retry_count < max_retries, it
  signals a retrieval retry instead of emitting a no-answer response.
- translate_agent: Unchanged logic from the original.
"""

import re
import time
from datetime import date
from typing import TypedDict, Any, Literal
from langgraph.graph import StateGraph, START, END
from .config import settings
from .corpus import active_release
from .retrieval import retrieve_queries, citation, expand_graph, normalize_query, tokens
from .providers import (
    privacy_gate, PrivacyBlocked, ProviderUnavailable,
    draft_and_verify, translate_checked, plan_queries,
)
from .schemas import Question, Answer, Claim
from .models import AnswerTrace, PrivateDocument, uid
from sqlalchemy import select
from .security import digest
from .localization import localize_explanations

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMERS = {
    'en': 'Information, not legal advice. Classification is provisional. Confirm requirements with the competent authority or a qualified IP facilitator.',
    'hi': 'यह जानकारी है, कानूनी सलाह नहीं। वर्गीकरण प्रारंभिक है। संबंधित प्राधिकरण या योग्य बौद्धिक संपदा विशेषज्ञ से पुष्टि करें।',
    'mr': 'ही माहिती आहे, कायदेशीर सल्ला नाही. वर्गीकरण प्राथमिक आहे. संबंधित प्राधिकरण किंवा पात्र बौद्धिक संपदा तज्ज्ञाकडून खात्री करा.',
}
HEADINGS = {
    'en': 'Evidence from your selected jurisdiction',
    'hi': 'न्यायक्षेत्र के अनुसार स्रोत',
    'mr': 'निवडलेल्या अधिकारक्षेत्रातील स्रोत',
}
PROMPT_VERSION = '2026.09.3-agentic-groq'

UNSAFE = re.compile(
    r'(ignore (?:all |previous |the )?instructions|reveal.*system prompt|bypass.*(?:consent|paywall)'
    r'|forge.*citation|fabricate.*(?:law|source)|make up.*(?:law|citation))',
    re.I,
)
CLINICAL = re.compile(
    r'(what dose|dosage for|treat my|cure my|diagnose me'
    r'|मुझे.*खुराक|माझा.*डोस)',
    re.I,
)
DOMAIN = re.compile(
    r'(patent|trademark|trade mark|copyright|design|geographic|\bgi\b|plant|variet'
    r'|trade secret|ayur|aahara|drug|cosmetic|formulat|biodivers|biological|\babs\b'
    r'|nagoya|\bcbd\b|gratk|\bpct\b|madrid|hague|budapest|trips|traditional'
    r'|knowledge|pharma|herbal|label|advert|export|licen|regulat|intellectual|\bip\b'
    r'|food|नियम|कायदा|आयुर्वेद)',
    re.I,
)

# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------

class State(TypedDict, total=False):
    question: Question
    db: Any
    rows: list
    citations: list
    claims: list
    stages: list[str]
    limitations: list[str]
    metrics: dict
    blocked: bool
    generated: bool
    translation: str | None
    # Cyclic-graph fields
    retry_count: int          # how many retrieval retries have been attempted
    max_retries: int          # ceiling on retrieval retries (default 2)
    needs_retry: bool         # compose → retrieve signal

# ---------------------------------------------------------------------------
# Agent 1: triage_agent  (replaces guard)
# ---------------------------------------------------------------------------

def triage_agent(state: State) -> dict:
    """
    Scope, safety, and privacy check.

    Replaces the old 'guard' node. Same keyword-level rules plus a future hook
    for LLM-assisted intent classification (when Groq is configured and the
    query is non-confidential and cloud_consent is True).
    """
    question = state['question']
    limitations: list[str] = []
    context = ' '.join(question.previous_questions + [question.query])

    domain_missing = (
        not DOMAIN.search(normalize_query(context))
        and settings().generation_provider == 'none'
    )
    blocked = bool(
        UNSAFE.search(context)
        or CLINICAL.search(question.query)
        or domain_missing
    )

    # AYUSH / nutraceutical carve-out
    if (
        re.search(r'\b(?:ASU|medicine|nutraceutical)\b', question.query, re.I)
        and not UNSAFE.search(context)
        and not CLINICAL.search(question.query)
    ):
        blocked = False

    # Hindi / Marathi unsafe patterns
    blocked = blocked or bool(
        re.search(
            r'(निर्देश.*(?:भूल|विसर)|कानून गढ़|कायदा बनवा|खुराक.*लेनी|तापासाठी.*डोस)',
            question.query,
        )
    )

    # Future-year authority
    years = [int(y) for y in re.findall(r'\b(20\d{2})\b', question.query)]
    if years and max(years) > date.today().year:
        blocked = True
        limitations.append(
            'The question refers to a future-dated authority that this corpus cannot verify.'
        )

    if blocked:
        limitations.append(
            'This assistant handles Ayurveda IP and regulatory information. '
            'It cannot provide clinical treatment, fabricated authority, or access-control bypasses.'
        )

    return {
        'blocked': blocked,
        'limitations': limitations,
        'stages': ['Scope and privacy triage'],
        'claims': [],
        'rows': [],
        'citations': [],
        'metrics': {},
        'generated': False,
        'translation': None,
        'retry_count': 0,
        'max_retries': 2,
        'needs_retry': False,
    }


def _route_after_triage(state: State) -> Literal['retrieve_agent', '__end__']:
    return '__end__' if state.get('blocked') else 'retrieve_agent'

# ---------------------------------------------------------------------------
# Agent 2: retrieve_agent  (replaces search, now cyclic)
# ---------------------------------------------------------------------------

def retrieve_agent(state: State) -> dict:
    """
    Jurisdiction-filtered hybrid retrieval with automatic retry expansion.

    On the first pass (retry_count == 0) it uses the raw question queries.
    On subsequent passes it uses LLM query-planning (via Groq) to expand the
    search space, and falls back to the broader 'treaties' market if the
    specific market returned nothing.
    """
    if state.get('blocked'):
        return {}

    q = state['question']
    retry_count = state.get('retry_count', 0)
    limitations = list(state.get('limitations', []))
    planned = False
    stages = list(state.get('stages', []))

    # Build query list
    queries = [q.query]
    if settings().generation_provider != 'none':
        try:
            privacy_gate(
                '\n'.join(q.previous_questions + [q.query]),
                q.confidential,
                q.cloud_consent,
                bool(q.case_id),
            )
            queries = plan_queries(q.query, q.jurisdiction, q.market, q.previous_questions)
            planned = True
        except (PrivacyBlocked, ProviderUnavailable) as error:
            limitations.append(str(error))
    elif q.previous_questions:
        queries.append(q.previous_questions[-1] + ' ' + q.query)

    # On retry: broaden market to 'treaties' if original market returned nothing
    market = q.market
    if retry_count > 0 and not state.get('rows'):
        market = 'treaties'
        stages.append(f'Retry {retry_count}: broadened market to treaties')

    rows, metrics = retrieve_queries(state['db'], queries, q.jurisdiction, market, q.as_of)
    rows, edges = expand_graph(state['db'], rows, q.jurisdiction, market, q.as_of)
    metrics['graph_edges'] = len(edges)
    metrics['llm_query_planning'] = planned
    metrics['retrieval_retry'] = retry_count

    new_stages = stages + (
        ['LLM search planning (Groq)'] if planned else []
    ) + ['Jurisdiction-filtered hybrid retrieval', 'Evidence-backed graph lookup']

    return {
        'rows': rows,
        'citations': [citation(r) for r in rows],
        'metrics': metrics,
        'limitations': limitations,
        'stages': new_stages,
        'needs_retry': False,  # reset signal
    }

# ---------------------------------------------------------------------------
# Agent 3: compose_agent  (replaces compose, now signals retry)
# ---------------------------------------------------------------------------

def compose_agent(state: State) -> dict:
    """
    LLM claim drafting → entailment verification.

    If 0 claims survive verification AND retry_count < max_retries, sets
    needs_retry=True to trigger another retrieval pass instead of returning
    a no-answer response immediately.
    """
    if state.get('blocked') or not state.get('citations'):
        # If we have no citations and retries are available, signal a retry.
        retry_count = state.get('retry_count', 0)
        max_retries = state.get('max_retries', 2)
        if not state.get('blocked') and retry_count < max_retries:
            return {
                'needs_retry': True,
                'retry_count': retry_count + 1,
                'stages': state.get('stages', []) + ['No evidence found — scheduling retrieval retry'],
            }
        return {}

    q = state['question']
    sources = state['citations']
    limitations = list(state.get('limitations', []))
    retry_count = state.get('retry_count', 0)
    max_retries = state.get('max_retries', 2)

    approved = [c for c in sources if c.review_status == 'approved' and not c.stale]
    evidence = sources if settings().reference_synthesis_enabled else approved
    claims: list = []
    generated = False
    attempted = False
    verification: dict = {}

    if settings().generation_provider != 'none' and evidence:
        try:
            privacy_gate(
                '\n'.join(q.previous_questions + [q.query]),
                q.confidential,
                q.cloud_consent,
                bool(q.case_id),
            )
            attempted = True
            private_facts = []  # Private documents are never sent to Groq (cloud provider)
            claims = draft_and_verify(
                q.query, evidence, q.jurisdiction, q.market,
                private_facts=private_facts,
                previous_questions=q.previous_questions,
                diagnostics=verification,
            )
            generated = bool(claims)

            # ── Cyclic retry signal ──────────────────────────────────────────
            # If LLM produced 0 verified claims and we still have retries left,
            # signal the graph to loop back to retrieve_agent with expanded terms.
            if not claims and retry_count < max_retries:
                return {
                    'needs_retry': True,
                    'retry_count': retry_count + 1,
                    'limitations': limitations,
                    'metrics': {
                        **state.get('metrics', {}),
                        'generation_attempted': attempted,
                        'verification': verification,
                    },
                    'stages': state.get('stages', []) + [
                        f'Verification returned 0 claims — retry {retry_count + 1}'
                    ],
                }
            # ────────────────────────────────────────────────────────────────

            if not claims:
                limitations.append(
                    'The generated answer could not be verified. '
                    'No answer has been released. Use the source library or request facilitator review.'
                )
        except (PrivacyBlocked, ProviderUnavailable) as error:
            limitations.append(str(error))

    elif settings().generation_provider != 'none' and not approved:
        limitations.append(
            'Current retrieved sources require applicability review '
            'before generated legal guidance can use them.'
        )
    else:
        limitations.append(
            'Generation is not configured. These are retrieved source excerpts, '
            'not a synthesized legal conclusion.'
        )

    # Extractive fallback (literal source spans, no LLM fabrication)
    if not generated and not attempted:
        query_terms = set(tokens(normalize_query(q.query)))
        for source in sources[:4]:
            sentences = [
                s for s in re.split(r'(?<=[.;।])\s+|\n\n', source.excerpt)
                if len(s.strip()) >= 60 and len(s.split()) >= 8
            ]
            sentences = [s for s in sentences if s.rstrip().endswith(('.', ';', '।'))]
            if re.search(r'\boral\b', q.query, re.I) and not re.search(r'\binject', q.query, re.I):
                sentences = [s for s in sentences if not re.search(r'\binjectable\b|\binjectables\b', s, re.I)]
            if not sentences:
                continue
            best = max(sentences, key=lambda s: len(set(tokens(s)) & query_terms), default=source.excerpt)
            if len(best) > 700:
                best = best[:700]
            claims.append({
                'text': best,
                'citation_ids': [source.id],
                'support_quote': best,
                'verification': 'extractive',
            })

    if any(c.review_status != 'approved' for c in sources):
        limitations.append(
            'Reference-library material has not been approved as current legal guidance. '
            'Check amendments and applicability before relying on it.'
        )
    if any(c.stale for c in sources):
        limitations.append('Some source checks are overdue; their current status is uncertain.')
    if generated and any(c.review_status != 'approved' or c.stale for c in evidence):
        limitations.append(
            'This is an AI synthesis of reference documents, not verified current-law guidance. '
            'Confirm applicability and amendments.'
        )

    return {
        'claims': claims,
        'generated': generated,
        'limitations': limitations,
        'needs_retry': False,
        'metrics': {
            **state.get('metrics', {}),
            'generation_attempted': attempted,
            'verification': verification,
        },
        'stages': state.get('stages', []) + ['Claim and citation validation (Groq)'],
    }


def _route_after_compose(state: State) -> Literal['retrieve_agent', 'translate_agent']:
    """Route back to retrieve_agent for a retry cycle, or forward to translate."""
    return 'retrieve_agent' if state.get('needs_retry') else 'translate_agent'

# ---------------------------------------------------------------------------
# Agent 4: translate_agent  (unchanged logic)
# ---------------------------------------------------------------------------

def translate_agent(state: State) -> dict:
    q = state['question']
    if q.language == 'en' or not state.get('generated'):
        return {}
    if q.confidential or q.case_id:
        return {
            'limitations': state.get('limitations', []) + [
                'Confidential answers are not sent to an external translation service. '
                'Original text is retained.'
            ]
        }
    try:
        translated = translate_checked(
            '\n'.join(c['text'] for c in state.get('claims', [])),
            q.language,
            q.cloud_consent,
        )
        return {
            'translation': translated,
            'stages': state.get('stages', []) + ['Translation reference checks'],
        }
    except (ProviderUnavailable, PrivacyBlocked) as error:
        return {'limitations': state.get('limitations', []) + [str(error)]}

# ---------------------------------------------------------------------------
# Build the LangGraph
# ---------------------------------------------------------------------------

builder = StateGraph(State)

# Register nodes
builder.add_node('triage_agent',   triage_agent)
builder.add_node('retrieve_agent', retrieve_agent)
builder.add_node('compose_agent',  compose_agent)
builder.add_node('translate_agent', translate_agent)

# Linear edges
builder.add_edge(START, 'triage_agent')
builder.add_edge('retrieve_agent', 'compose_agent')
builder.add_edge('translate_agent', END)

# Conditional edges (the cyclic part)
builder.add_conditional_edges(
    'triage_agent',
    _route_after_triage,
    {'retrieve_agent': 'retrieve_agent', '__end__': END},
)
builder.add_conditional_edges(
    'compose_agent',
    _route_after_compose,
    {'retrieve_agent': 'retrieve_agent', 'translate_agent': 'translate_agent'},
)

workflow = builder.compile()

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def answer_question(db, q: Question, session_id=None) -> Answer:
    start = time.perf_counter()
    state = workflow.invoke(
        {'question': q, 'db': db},
        {'recursion_limit': 12},  # higher limit allows up to 2 retry cycles
    )
    release = active_release(db)
    trace_id = uid()

    # Return only citations that actually appear in the released answer.
    cited = {i for c in state.get('claims', []) for i in c['citation_ids']}
    citations = [c for c in state.get('citations', []) if c.id in cited]

    mode = (
        'generated' if state.get('generated')
        else 'retrieval' if state.get('claims')
        else 'abstention'
    )
    fully_reviewed = all(c.review_status == 'approved' and not c.stale for c in citations)
    status = (
        'supported' if state.get('generated') and fully_reviewed
        else 'partial' if state.get('claims')
        else 'insufficient'
    )
    limitations = list(dict.fromkeys(
        s.strip() for s in state.get('limitations', [])
        if isinstance(s, str) and s.strip()
    ))
    if not state.get('claims') and not state.get('blocked') and not state.get('metrics', {}).get('generation_attempted'):
        limitations.append(
            'Information not found in the current corpus for this jurisdiction. '
            'No legal conclusion has been generated.'
        )
    if q.language != 'en' and not state.get('translation'):
        limitations.append(
            'Original source language is retained. '
            'Interface language does not imply that these excerpts are translated.'
        )

    cfg = settings()
    model_name = cfg.groq_model if cfg.generation_provider == 'groq' else None
    metrics = {
        **state.get('metrics', {}),
        'elapsed_ms': round((time.perf_counter() - start) * 1000),
        'generation_provider': cfg.generation_provider,
        'generation_model': model_name,
        'retrieval_retries': state.get('retry_count', 0),
    }

    result = Answer(
        trace_id=trace_id,
        mode=mode,
        jurisdiction=q.jurisdiction,
        market=q.market,
        language=q.language,
        heading=(
            HEADINGS[q.language] if mode != 'abstention'
            else {'en': 'More evidence is needed',
                  'hi': 'अधिक साक्ष्य की आवश्यकता है',
                  'mr': 'अधिक पुराव्याची आवश्यकता आहे'}[q.language]
        ),
        claims=[Claim(**c) for c in state.get('claims', [])],
        citations=citations,
        evidence_status=status,
        evidence_reasons=[
            'AI synthesis linked to retrieved passages; entailment checked. '
            + ('Source applicability reviewed.' if fully_reviewed else 'Source applicability remains unreviewed.')
            if state.get('generated')
            else 'Literal excerpts available; applicability review required.'
            if state.get('claims')
            else 'No sufficient evidence for a supported answer.'
        ],
        limitations=limitations,
        next_steps=[
            'Open the cited source and check its version.',
            'Use the formulation or ABS assessment for product-specific routing.',
            'Export your case or request facilitator review if uncertainty remains.',
        ],
        disclaimer=DISCLAIMERS[q.language],
        corpus_release=release.id if release else None,
        translation=state.get('translation'),
        stages=state.get('stages', []),
        metrics=metrics,
    )

    db.add(AnswerTrace(
        id=trace_id,
        session_id=session_id,
        query_hash=digest(q.query),
        jurisdiction=q.jurisdiction,
        market=q.market,
        language=q.language,
        model=cfg.generation_provider,
        prompt_version=PROMPT_VERSION,
        release_id=release.id if release else None,
        citation_ids=[c.id for c in citations],
        outcome=mode,
        metrics=metrics,
    ))
    db.commit()

    return Answer(**localize_explanations(result.model_dump(), q.language))
