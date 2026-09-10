"""Initial relational schema and PostgreSQL search indexes."""
from alembic import op
from app.db import Base
from app import models
revision = '0001'
down_revision = None

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql': op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    Base.metadata.create_all(bind)
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TABLE chunks ADD COLUMN search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(heading,'') || ' ' || text)) STORED")
        op.execute('CREATE INDEX chunks_search_idx ON chunks USING gin(search_vector)')
        op.execute('ALTER TABLE chunks ADD COLUMN vector_embedding vector(384)')
        op.execute('CREATE INDEX chunks_vector_idx ON chunks USING hnsw(vector_embedding vector_cosine_ops)')
        op.execute('CREATE UNIQUE INDEX one_active_release ON corpus_releases (active) WHERE active = true')

def downgrade():
    Base.metadata.drop_all(op.get_bind())
