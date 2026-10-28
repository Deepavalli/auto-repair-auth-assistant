"""
Guideline lookup used by the agent.

  find_guideline(code, carrier) - exact code match for the claim's carrier (no cross-carrier fallback)
  semantic_search(query)        - nearest guideline by embedding (pgvector),
                                  only when ENABLE_SEMANTIC_SEARCH=true
"""
import os

from sqlalchemy import select, func

from db.database import SessionLocal
from db.models import GuidelineRecord
from data.coverage_guidelines import CoverageGuideline

SEMANTIC_ENABLED = os.getenv("ENABLE_SEMANTIC_SEARCH", "false").lower() == "true"
MAX_DISTANCE = float(os.getenv("SEMANTIC_MAX_DISTANCE", "0.5"))  # cosine distance


def find_guideline(service_code: str, carrier_name: str | None = None) -> CoverageGuideline | None:
    """Exact code match for the claim's carrier.

    Never falls back to another carrier's guideline: carriers have different
    rules, so a missing guideline means "route to an adjuster", not "borrow one".
    """
    query = select(GuidelineRecord).where(
        func.upper(GuidelineRecord.service_code) == service_code.upper()
    )
    if carrier_name:
        query = query.where(func.lower(GuidelineRecord.carrier_name) == carrier_name.strip().lower())
    with SessionLocal() as session:
        row = session.execute(query.limit(1)).scalars().first()
    return to_domain(row) if row else None


def semantic_search(query_text: str, carrier_name: str | None = None) -> CoverageGuideline | None:
    if not SEMANTIC_ENABLED:
        return None
    from db.embeddings import available, embed
    if not available():
        return None
    vec = embed(query_text)
    distance = GuidelineRecord.embedding.cosine_distance(vec)
    query = (select(GuidelineRecord, distance.label("d"))
             .where(GuidelineRecord.embedding.is_not(None)))
    if carrier_name:
        query = query.where(func.lower(GuidelineRecord.carrier_name) == carrier_name.strip().lower())
    with SessionLocal() as session:
        row = session.execute(query.order_by(distance).limit(1)).first()
    if row is None or row.d > MAX_DISTANCE:
        return None
    return to_domain(row[0])


def list_all() -> list[CoverageGuideline]:
    with SessionLocal() as session:
        rows = session.execute(select(GuidelineRecord).order_by(GuidelineRecord.service_code)).scalars().all()
        return [to_domain(r) for r in rows]


def to_domain(rec: GuidelineRecord) -> CoverageGuideline:
    return CoverageGuideline(
        guideline_id=rec.guideline_id,
        carrier_name=rec.carrier_name,
        service_code=rec.service_code,
        service_name=rec.service_name,
        preapproval_required=rec.preapproval_required,
        criteria=rec.criteria or [],
        guideline_text=rec.guideline_text,
    )
