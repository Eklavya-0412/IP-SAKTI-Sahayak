from typing import Literal, Any
from pydantic import BaseModel, Field, EmailStr, model_validator

Language = Literal['en', 'hi', 'mr']
Jurisdiction = Literal['india', 'international']
Market = Literal['treaties', 'us', 'eu', 'uk']

class Question(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    jurisdiction: Jurisdiction = 'india'
    market: Market = 'treaties'
    language: Language = 'en'
    case_id: str | None = None
    confidential: bool = False
    cloud_consent: bool = False
    previous_questions: list[str] = Field(default_factory=list, max_length=4)
    as_of: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    @model_validator(mode='after')
    def normalize(self):
        self.query = self.query.strip()
        if len(self.query) < 3: raise ValueError('Enter a substantive question')
        if any(len(q)>4000 for q in self.previous_questions): raise ValueError('Conversation context is too long')
        if self.jurisdiction == 'india': self.market = 'treaties'
        if self.as_of:
            from datetime import date
            date.fromisoformat(self.as_of)
        return self

class Citation(BaseModel):
    id: str
    source_id: str
    version_id: str
    title: str
    publisher: str
    url: str
    locator: str
    page: int | None
    excerpt: str
    authority: str
    jurisdiction: str
    market: str
    retrieved_at: str
    review_status: str
    stale: bool

class Claim(BaseModel):
    kind: Literal['explanation', 'clarification'] = 'explanation'
    text: str
    citation_ids: list[str]
    support_quote: str
    verification: str = 'extractive'

class Answer(BaseModel):
    trace_id: str
    mode: Literal['retrieval', 'generated', 'abstention']
    jurisdiction: Jurisdiction
    market: Market
    language: Language
    answer_language: Language = 'en'
    heading: str
    claims: list[Claim] = []
    citations: list[Citation] = []
    evidence_status: Literal['supported', 'partial', 'insufficient']
    evidence_reasons: list[str] = []
    limitations: list[str] = []
    next_steps: list[str] = []
    disclaimer: str
    corpus_release: str | None = None
    translation: str | None = None
    stages: list[str] = []
    metrics: dict = {}

class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

class CaseInput(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    jurisdiction: Jurisdiction = 'india'
    market: Market = 'treaties'
    confidential: bool = True
    content: dict[str, Any] = Field(default_factory=dict)

class AssessmentInput(BaseModel):
    assessment_id: str | None = None
    answers: dict[str, str] = Field(default_factory=dict)
    language: Language = 'en'

class ConsentInput(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    scope: Literal['search', 'read', 'private_import', 'translation', 'speech']
    purpose: str = Field(min_length=10, max_length=500)
    days: int = Field(default=30, ge=1, le=90)
