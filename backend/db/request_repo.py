"""Postgres-backed store for processed repair-authorization requests."""
from sqlalchemy import select

from api.decisions import compute_disposition
from api.schemas import RepairAuthResult, CriterionResult
from db.database import SessionLocal
from db.models import RequestRecord


def save(result: RepairAuthResult) -> None:
    with SessionLocal() as session:
        session.add(RequestRecord(
            id=result.id,
            claim_number=result.claim_number,
            policyholder_name=result.policyholder_name,
            carrier_name=result.carrier_name,
            vehicle=result.vehicle,
            service_code=result.service_code,
            service_name=result.service_name,
            estimated_cost=result.estimated_cost,
            note_text=result.note_text,
            preapproval_required=result.preapproval_required,
            guideline_id=result.guideline_id,
            confidence=result.confidence,
            draft=result.draft,
            criteria=[c.model_dump() for c in result.criteria],
            trace=result.trace,
            created_at=result.created_at,
        ))
        session.commit()


def list_all() -> list[RepairAuthResult]:
    with SessionLocal() as session:
        rows = session.execute(
            select(RequestRecord).order_by(RequestRecord.created_at.desc())
        ).scalars().all()
        return [to_schema(r) for r in rows]


def get(request_id: str) -> RepairAuthResult | None:
    with SessionLocal() as session:
        r = session.get(RequestRecord, request_id)
        return to_schema(r) if r else None


def apply_override(request_id: str, decision: str, reason: str, reviewer: str) -> RepairAuthResult | None:
    with SessionLocal() as session:
        r = session.get(RequestRecord, request_id)
        if r is None:
            return None
        r.overridden = True
        r.override_decision = decision
        r.override_reason = reason
        r.override_by = reviewer
        session.commit()
        session.refresh(r)
        return to_schema(r)


def to_schema(r: RequestRecord) -> RepairAuthResult:
    return RepairAuthResult(
        id=r.id,
        claim_number=r.claim_number,
        policyholder_name=r.policyholder_name,
        carrier_name=r.carrier_name,
        vehicle=r.vehicle,
        service_code=r.service_code,
        service_name=r.service_name,
        estimated_cost=r.estimated_cost,
        note_text=r.note_text,
        preapproval_required=r.preapproval_required,
        guideline_id=r.guideline_id,
        criteria=[CriterionResult(**c) for c in (r.criteria or [])],
        draft=r.draft,
        confidence=r.confidence,
        trace=r.trace or [],
        created_at=r.created_at,
        disposition=compute_disposition(r.preapproval_required, r.confidence,
                                        bool(r.overridden), r.override_decision),
        overridden=bool(r.overridden),
        override_decision=r.override_decision,
        override_reason=r.override_reason,
        override_by=r.override_by,
    )
