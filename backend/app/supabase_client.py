"""
Supabase client — thin wrapper for Auth / Realtime / Storage features.

For core RAG retrieval we use SQLAlchemy directly against Supabase's Postgres
endpoint (via DATABASE_URL), which is more efficient for vector search.
This client is intended for future Auth and Realtime integrations.

Usage:
    from .supabase_client import get_supabase_client
    client = get_supabase_client()
    # client.auth.sign_in_with_password(...)
    # client.table('sources').select('*').execute()
"""
from functools import lru_cache
from .config import settings


@lru_cache(maxsize=1)
def get_supabase_client():
    """Return a cached Supabase client. Returns None if not configured."""
    cfg = settings()
    if not cfg.supabase_url or not cfg.supabase_anon_key:
        return None
    try:
        from supabase import create_client, Client  # type: ignore
        client: Client = create_client(cfg.supabase_url, cfg.supabase_anon_key)
        return client
    except ImportError:
        # supabase-py not installed — graceful degradation
        return None
    except Exception:
        return None
