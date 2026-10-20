import os

import pytest

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="requires TEST_DATABASE_URL pointing at a real Postgres+pgvector instance",
)


def test_hnsw_index_is_created_by_migration_and_used_by_the_planner():
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(cfg, "head")

    engine = create_engine(TEST_DATABASE_URL)
    try:
        with engine.connect() as conn:
            index_names = conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE tablename = 'chunks'")
            ).scalars().all()
            assert "ix_chunks_embedding_hnsw" in index_names

            conn.execute(text("SET hnsw.iterative_scan = 'relaxed_order'"))
            zero_vector = "[" + ",".join(["0"] * 1536) + "]"
            plan_rows = conn.execute(
                text(
                    "EXPLAIN SELECT id FROM chunks ORDER BY embedding <=> :q LIMIT 5"
                ),
                {"q": zero_vector},
            ).scalars().all()
            plan_text = "\n".join(plan_rows)
            assert "ix_chunks_embedding_hnsw" in plan_text
    finally:
        command.downgrade(cfg, "d2b3c4e5f6a7")
        engine.dispose()
