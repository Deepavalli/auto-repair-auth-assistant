"""
Service layer: turns an API submission into a ClaimFile, runs the agent,
converts the final state into a RepairAuthResult, and saves it.
Route handlers stay thin and just call these functions.
"""
import re
import uuid
from datetime import datetime, timezone

from agent.appeal import draft_appeal
from agent.graph import agent
from api.decisions import compute_disposition
from api.schemas import SubmitRequest, RepairAuthResult, CriterionResult, BatchItemResult
from data.coverage_guidelines import CARRIER
from db import request_repo
from models.acord import (
    ClaimFile, PolicyHolder, Vehicle, AutoPolicy, Loss, RepairRequest,
)


def _parse_vehicle(text: str | None) -> Vehicle:
    """Best-effort parse of '2022 Honda CR-V'."""
    if not text:
        return Vehicle()
    m = re.match(r"\s*(\d{4})\s+(\S+)\s*(.*)", text)
    if m:
        return Vehicle(year=int(m.group(1)), make=m.group(2), model=m.group(3).strip())
    return Vehicle(model=text.strip())


def build_claim(req: SubmitRequest) -> ClaimFile:
    first, _, last = req.policyholder_name.strip().partition(" ")
    return ClaimFile(
        claim_number=req.claim_number or "CLM-" + uuid.uuid4().hex[:8].upper(),
        policyholder=PolicyHolder(id="PH-" + uuid.uuid4().hex[:6], first_name=first, last_name=last),
        vehicle=_parse_vehicle(req.vehicle),
        policy=AutoPolicy(policy_number="UNKNOWN", carrier_name=req.carrier_name or CARRIER),
        loss=Loss(),
        repair_request=RepairRequest(
            service_code=req.service_code,
            service_name=req.service_name,
            estimated_cost=req.estimated_cost,
        ),
        note_text=req.note_text,
    )


def run_agent(claim: ClaimFile) -> dict:
    return agent.invoke({"claim": claim})


def process_submission(req: SubmitRequest, save: bool = True) -> RepairAuthResult:
    """Run one request through the agent. save=False is a dry run (not stored)."""
    claim = build_claim(req)
    final = run_agent(claim)
    guideline = final.get("matched_guideline")
    preapproval = bool(final.get("preapproval_required"))
    confidence = final.get("confidence")

    result = RepairAuthResult(
        id=uuid.uuid4().hex[:12],
        claim_number=claim.claim_number,
        policyholder_name=req.policyholder_name,
        carrier_name=claim.policy.carrier_name,
        vehicle=req.vehicle,
        service_code=final.get("service_code", req.service_code),
        service_name=req.service_name,
        estimated_cost=req.estimated_cost,
        note_text=req.note_text,
        preapproval_required=preapproval,
        guideline_id=guideline.guideline_id if guideline else None,
        criteria=[CriterionResult(**c) for c in final.get("criteria_checks", [])],
        draft=final.get("draft"),
        confidence=confidence,
        disposition=compute_disposition(preapproval, confidence),
        trace=final.get("trace", []),
        created_at=datetime.now(timezone.utc),
    )
    if save:
        request_repo.save(result)
    return result


def process_batch_item(index: int, req: SubmitRequest) -> BatchItemResult:
    """Never raises: a failure in one item must not sink the rest of the batch."""
    try:
        result = process_submission(req)
        return BatchItemResult(index=index, policyholder_name=req.policyholder_name,
                               service_name=req.service_name, ok=True, result=result)
    except Exception as exc:  # noqa: BLE001 - reported per item to the caller
        return BatchItemResult(index=index, policyholder_name=req.policyholder_name,
                               service_name=req.service_name, ok=False,
                               error=f"{type(exc).__name__}: {exc}")


def appeal_for(request_id: str) -> str | None:
    result = request_repo.get(request_id)
    if result is None:
        return None
    return draft_appeal(result)


def analytics() -> dict:
    rows = request_repo.list_all()
    by_disposition: dict[str, int] = {}
    by_service: dict[str, int] = {}
    for r in rows:
        by_disposition[r.disposition] = by_disposition.get(r.disposition, 0) + 1
        by_service[r.service_name] = by_service.get(r.service_name, 0) + 1
    scored = [r.confidence for r in rows if r.preapproval_required and r.confidence is not None]
    return {
        "total_requests": len(rows),
        "preapproval_required": sum(1 for r in rows if r.preapproval_required),
        "preapproval_not_required": sum(1 for r in rows if not r.preapproval_required),
        "overridden": sum(1 for r in rows if r.overridden),
        "avg_confidence": round(sum(scored) / len(scored), 2) if scored else 0,
        "total_estimated_cost": round(sum(r.estimated_cost or 0 for r in rows), 2),
        "by_disposition": by_disposition,
        "by_service": by_service,
    }
