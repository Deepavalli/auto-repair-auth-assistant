from datetime import datetime, timezone

from api.acord import to_acord
from api.decisions import compute_disposition
from api.schemas import RepairAuthResult, CriterionResult, SubmitRequest
from api.service import build_claim


def test_disposition_rules():
    assert compute_disposition(False, None) == "no-preapproval-required"
    assert compute_disposition(True, 1.0) == "approved"
    assert compute_disposition(True, 0.67) == "pended"
    assert compute_disposition(True, 0.2, True, "APPROVED") == "approved"


def test_build_claim_parses_vehicle():
    claim = build_claim(SubmitRequest(
        policyholder_name="Maria Lopez", service_code="auto-gls-rpl",
        service_name="Windshield replacement", note_text="x", vehicle="2022 Honda CR-V",
        estimated_cost=1180))
    assert claim.vehicle.year == 2022 and claim.vehicle.make == "Honda"
    assert claim.policy.carrier_name == "Lakeshore Mutual Auto"
    assert "$1,180.00" in claim.facts()


def test_acord_mapping():
    r = RepairAuthResult(
        id="abc", claim_number="CLM-1", policyholder_name="A B", service_code="X",
        service_name="Y", note_text="n", preapproval_required=True,
        criteria=[CriterionResult(criterion="c", status="met", justification="j")],
        confidence=1.0, disposition="approved", trace=[], created_at=datetime.now(timezone.utc))
    out = to_acord(r)["ClaimsSvcRs"]["RepairAuthorization"]
    assert out["Disposition"] == "approved"
    assert out["CriteriaEvaluation"][0]["Status"] == "met"
