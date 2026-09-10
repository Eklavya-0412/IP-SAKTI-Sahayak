"""Application settings — loaded from .env via pydantic-settings."""
from pathlib import Path
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')

    app_env: str = 'development'

    # ── Database (Supabase PostgreSQL) ────────────────────────────────────────
    # Required: postgresql+psycopg://user:pass@host:port/dbname
    database_url: str = ''

    # ── Supabase project (Auth / Realtime / Storage) ─────────────────────────
    supabase_url: str = ''
    supabase_anon_key: str = ''

    # ── Session / Security ────────────────────────────────────────────────────
    session_secret: str = 'development-only-change-before-deployment'
    public_origin: str = 'http://127.0.0.1:5173'
    cookie_secure: bool = False
    storage_dir: Path = ROOT / 'data'
    corpus_manifest: Path = ROOT / 'corpus' / 'manifest.json'

    @field_validator('storage_dir', mode='before')
    @classmethod
    def _validate_storage_dir(cls, v):
        if not v or str(v).strip() in ('', '.'):
            return ROOT / 'data'
        return Path(v)

    @field_validator('corpus_manifest', mode='before')
    @classmethod
    def _validate_corpus_manifest(cls, v):
        if not v or str(v).strip() in ('', '.'):
            return ROOT / 'corpus' / 'manifest.json'
        return Path(v)

    # ── Generation provider — "groq" | "none" ────────────────────────────────
    generation_provider: str = 'groq'
    groq_api_key: str = ''
    groq_model: str = 'llama-3.1-70b-versatile'
    generation_timeout_seconds: int = 90

    # ── Ingestion (LlamaParse) ────────────────────────────────────────────────
    llama_cloud_api_key: str = ''
    # LlamaParse result type: "markdown" is required for the header splitter
    llama_parse_result_type: str = 'markdown'
    # Chunking parameters
    chunk_size: int = 1500
    chunk_overlap: int = 200

    # ── Embeddings (local sentence-transformers) ──────────────────────────────
    embeddings_enabled: bool = True
    reference_synthesis_enabled: bool = True
    embedding_model: str = 'intfloat/multilingual-e5-small'
    embedding_revision: str = '614241f622f53c4eeff9890bdc4f31cfecc418b3'

    # ── Bhashini (Translation) ────────────────────────────────────────────────
    bhashini_user_id: str = ''
    bhashini_api_key: str = ''
    bhashini_pipeline_id: str = ''
    bhashini_config_url: str = 'https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline'

    # ── Admin / Retention ─────────────────────────────────────────────────────
    admin_email: str = ''
    admin_password: str = ''
    guest_retention_hours: int = 24
    case_retention_days: int = 90
    audit_retention_days: int = 365
    max_upload_mb: int = 15
    daily_request_limit: int = 100
    requests_per_minute: int = 20
    source_stale_days: int = 30

    def validate_deployment(self):
        if self.app_env == 'production':
            if (
                len(self.session_secret) < 32
                or self.session_secret.startswith('development')
                or 'replace-with' in self.session_secret
            ):
                raise RuntimeError('Set a random SESSION_SECRET of at least 32 characters.')
            if not self.cookie_secure or not self.public_origin.startswith('https://'):
                raise RuntimeError('Production requires HTTPS PUBLIC_ORIGIN and COOKIE_SECURE=true.')
            if not self.database_url.startswith('postgresql'):
                raise RuntimeError('Production requires a PostgreSQL DATABASE_URL.')
            if not self.groq_api_key:
                raise RuntimeError('Production requires GROQ_API_KEY.')


@lru_cache
def settings():
    return Settings()
