"""
ACORD-inspired domain models for an auto (vehicle) insurance claim.

ACORD is the data standard used across the P&C insurance industry. These
classes borrow its vocabulary (policy, insured, vehicle, loss, coverage)
without implementing a full ACORD schema - enough to be authentic to the
domain while staying readable.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class PolicyHolder(BaseModel):
    """The insured person (ACORD: InsuredOrPrincipal)."""
    id: str
    first_name: str
    last_name: str


class Vehicle(BaseModel):
    """The insured vehicle (ACORD: PersVeh)."""
    vin: str = "UNKNOWN"
    year: Optional[int] = None
    make: str = ""
    model: str = ""
    adas_equipped: Optional[bool] = Field(None, description="Has driver-assist cameras/sensors")
    actual_cash_value: Optional[float] = Field(None, description="Pre-loss market value (ACV), USD")

    def label(self) -> str:
        parts = [str(self.year) if self.year else "", self.make, self.model]
        return " ".join(p for p in parts if p).strip() or "Unknown vehicle"


class Coverage(BaseModel):
    """One coverage on the auto policy (ACORD: Coverage)."""
    type: str = Field(description="collision | comprehensive | rental | towing | liability")
    deductible: float = 0
    limit: Optional[float] = None


class AutoPolicy(BaseModel):
    """The auto policy the claim is made under (ACORD: PersAutoPolicy)."""
    policy_number: str
    carrier_name: str
    coverages: list[Coverage] = Field(default_factory=list)


class Loss(BaseModel):
    """What happened (ACORD: ClaimsOccurrence)."""
    loss_date: Optional[date] = None
    cause: str = Field("", description="collision | glass | hail | theft | other")
    description: str = ""


class RepairRequest(BaseModel):
    """The repair operation the shop wants authorized."""
    service_code: str = Field(description="Internal repair-operation code, e.g. AUTO-GLS-RPL")
    service_name: str
    estimated_cost: Optional[float] = Field(None, description="Shop estimate, USD")
    reason: str = ""


class ClaimFile(BaseModel):
    """Everything the agent needs: the full input bundle."""
    claim_number: str
    policyholder: PolicyHolder
    vehicle: Vehicle
    policy: AutoPolicy
    loss: Loss
    repair_request: RepairRequest
    note_text: str = Field(description="Free-text estimator/adjuster narrative")

    def facts(self) -> str:
        """Structured facts rendered as text for the LLM prompts."""
        cov = ", ".join(
            f"{c.type} (deductible ${c.deductible:,.0f})" for c in self.policy.coverages
        ) or "not provided"
        est = (f"${self.repair_request.estimated_cost:,.2f}"
               if self.repair_request.estimated_cost is not None else "not provided")
        acv = (f"${self.vehicle.actual_cash_value:,.2f}"
               if self.vehicle.actual_cash_value is not None else "not provided")
        adas = {True: "yes", False: "no", None: "not stated"}[self.vehicle.adas_equipped]
        return (
            f"Claim number: {self.claim_number}\n"
            f"Carrier: {self.policy.carrier_name}\n"
            f"Policy coverages: {cov}\n"
            f"Vehicle: {self.vehicle.label()} (ADAS equipped: {adas}, actual cash value: {acv})\n"
            f"Loss: {self.loss.cause or 'not stated'} on {self.loss.loss_date or 'date not stated'}\n"
            f"Requested repair: {self.repair_request.service_name} ({self.repair_request.service_code})\n"
            f"Estimated cost: {est}"
        )
