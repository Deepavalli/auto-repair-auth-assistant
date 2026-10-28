"""
ACORD-inspired JSON view of a decision, for carrier/partner integrations.

ACORD is the P&C insurance data standard. This is a readable, simplified
representation that borrows ACORD vocabulary (InsuredOrPrincipal, PersVeh,
ClaimsOccurrence...). It is NOT a conformant ACORD XML/JSON message; treat
it as the mapping layer to extend toward a real ACORD integration.
"""
from api.schemas import RepairAuthResult


def to_acord(result: RepairAuthResult) -> dict:
    return {
        "standard": "ACORD-inspired (simplified, non-conformant)",
        "ClaimsSvcRs": {
            "RqUID": result.id,
            "ClaimsOccurrence": {
                "ItemIdInfo": {"InsurerId": result.claim_number},
                "CarrierName": result.carrier_name,
            },
            "InsuredOrPrincipal": {"GeneralPartyInfo": {"NameInfo": result.policyholder_name}},
            "PersVeh": {"Description": result.vehicle},
            "RepairAuthorization": {
                "ServiceCd": result.service_code,
                "ServiceDesc": result.service_name,
                "EstimatedAmt": {"Amt": result.estimated_cost, "CurCd": "USD"},
                "PreApprovalRequiredInd": result.preapproval_required,
                "GuidelineId": result.guideline_id,
                "Disposition": result.disposition,
                "ConfidenceScore": result.confidence,
                "CriteriaEvaluation": [
                    {"Criterion": c.criterion, "Status": c.status, "Remark": c.justification}
                    for c in result.criteria
                ],
                "ReviewerOverride": {
                    "OverriddenInd": result.overridden,
                    "Decision": result.override_decision,
                    "Reason": result.override_reason,
                    "Reviewer": result.override_by,
                },
            },
        },
    }
