"""
One-time setup: enable pgvector, create tables, seed the synthetic guidelines.
Embeddings are added when sentence-transformers is installed
(requirements-ml.txt); otherwise guidelines are seeded without them.

Run: python -m db.init_db
"""
from sqlalchemy import text

from db.database import engine, SessionLocal, Base
from db import models  # noqa: F401  (registers tables)
from db.models import GuidelineRecord
from db.embeddings import available, embed
from data.coverage_guidelines import GUIDELINES


def init() -> None:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    print("pgvector extension ready")

    Base.metadata.create_all(engine)
    print("tables created")

    use_embeddings = available()
    if not use_embeddings:
        print("sentence-transformers not installed: seeding without embeddings")

    added = 0
    with SessionLocal() as session:
        for g in GUIDELINES:
            if session.get(GuidelineRecord, g.guideline_id):
                continue
            session.add(GuidelineRecord(
                guideline_id=g.guideline_id,
                carrier_name=g.carrier_name,
                service_code=g.service_code,
                service_name=g.service_name,
                preapproval_required=g.preapproval_required,
                criteria=g.criteria,
                guideline_text=g.guideline_text,
                embedding=embed(g.guideline_text) if use_embeddings else None,
            ))
            added += 1
        session.commit()
    print(f"seeded {added} new guidelines ({len(GUIDELINES)} defined)")


if __name__ == "__main__":
    init()
