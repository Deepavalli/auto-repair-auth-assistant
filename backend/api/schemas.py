"""API contracts (kept separate from the internal ACORD-style models)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SubmitRequest(BaseModel):
    """What the repair shop / claims desk submits."""
    policyholder_name: str
    service_code: str = Field(description="Repair-operation code, e.g. AUTO-GLS-RPL")
    service_name: str
    note_text: str = Field(description="Estimator / adjuster narrative")
    carrier_name: Optional[str] = None
    claim_number: Optional[str] = None
    vehicle: Optional[str] = Field(None, description='e.g. "2022 Honda CR-V"')
    estimated_cost: Optional[float] = None


class CriterionResult(BaseModel):
    criterion: str
    status: str
    justification: str


class RepairAuthResult(BaseModel):
    id: str
    claim_number: str
    policyholder_name: str
    carrier_name: Optional[str] = None
    vehicle: Optional[str] = None
    service_code: str
    service_name: str
    estimated_cost: Optional[float] = None
    note_text: str
    preapproval_required: bool
    guideline_id: Optional[str] = None
    criteria: list[CriterionResult]
    draft: Optional[str] = None
    confidence: Optional[float] = None
    disposition: str
    trace: list[str]
    created_at: datetime
    overridden: bool = False
    override_decision: Optional[str] = None
    override_reason: Optional[str] = None
    override_by: Optional[str] = None


class OverrideRequest(BaseModel):
    request_id: str
    decision: Literal["APPROVED", "DENIED"]
    reason: str
    reviewer: str


class AppealRequest(BaseModel):
    request_id: str


class BatchItemResult(BaseModel):
    """One entry of a batch run: either a result or an error, never both."""
    index: int
    policyholder_name: str
    service_name: str
    ok: bool
    result: Optional[RepairAuthResult] = None
    error: Optional[str] = None
