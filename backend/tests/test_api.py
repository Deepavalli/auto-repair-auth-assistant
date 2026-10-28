"""
API route tests (review finding #11). The agent and database are replaced
with in-memory fakes, so no Claude key or Postgres is needed.
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import api.main as main
import api.service as service
from api.schemas import RepairAuthResult, SubmitRequest

STORE: dict[str, RepairAuthResult] = {}


def _fake_result(req: SubmitRequest, rid: str) -> RepairAuthResult:
    return RepairAuthResult(
        id=rid, claim_number="CLM-TEST", policyholder_name=req.policyholder_name,
        service_code=req.service_code, service_name=req.service_name, note_text=req.note_text,
        preapproval_required=True, criteria=[], confidence=1.0, disposition="approved",
        trace=[], created_at=datetime.now(timezone.utc))


@pytest.fixture
def client(monkeypatch):
    STORE.clear()

    def fake_process(req, save=True):
        if req.policyholder_name == "BOOM":
            raise RuntimeError("Claude unavailable")
        r = _fake_result(req, f"id{len(STORE)}")
        if save:
            STORE[r.id] = r
        return r

    def fake_override(rid, decision, reason, reviewer):
        r = STORE.get(rid)
        if r is None:
            return None
        r = r.model_copy(update={"overridden": True, "override_decision": decision,
                                 "override_reason": reason, "override_by": reviewer,
                                 "disposition": decision.lower()})
        STORE[rid] = r
        return r

    monkeypatch.setattr(service, "process_submission", fake_process)
    monkeypatch.setattr(main.request_repo, "get", lambda rid: STORE.get(rid))
    monkeypatch.setattr(main.request_repo, "list_all", lambda: list(STORE.values()))
    monkeypatch.setattr(main.request_repo, "apply_override", fake_override)
    monkeypatch.setattr(main, "REVIEWER_API_KEY", "")
    return TestClient(main.app)


BODY = {"policyholder_name": "Maria Lopez", "service_code": "AUTO-GLS-RPL",
        "service_name": "Windshield replacement", "note_text": "crack"}


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_submit_saves_and_dry_run_does_not(client):
    assert client.post("/api/submit", json=BODY).status_code == 200
    assert client.post("/api/submit?save=false", json=BODY).status_code == 200
    assert len(STORE) == 1  # review finding #9


def test_batch_reports_failures_per_item(client):
    """Review finding #4: one failure must not sink the batch."""
    r = client.post("/api/batch", json=[BODY, {**BODY, "policyholder_name": "BOOM"}, BODY])
    assert r.status_code == 200
    items = r.json()
    assert [i["ok"] for i in items] == [True, False, True]
    assert "Claude unavailable" in items[1]["error"]
    assert [i["index"] for i in items] == [0, 1, 2]


def test_batch_size_limit(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_BATCH_SIZE", 2)
    assert client.post("/api/batch", json=[BODY] * 3).status_code == 413


def test_override_and_acord(client):
    rid = client.post("/api/submit", json=BODY).json()["id"]
    r = client.post("/api/override", json={"request_id": rid, "decision": "DENIED",
                                           "reason": "photos unclear", "reviewer": "J. Carter"})
    assert r.status_code == 200 and r.json()["disposition"] == "denied"
    acord = client.get(f"/api/requests/{rid}/acord").json()
    assert acord["ClaimsSvcRs"]["RepairAuthorization"]["ReviewerOverride"]["OverriddenInd"] is True


def test_override_requires_reviewer_key_when_configured(client, monkeypatch):
    """Review finding #12."""
    monkeypatch.setattr(main, "REVIEWER_API_KEY", "s3cret")
    rid = client.post("/api/submit", json=BODY).json()["id"]
    body = {"request_id": rid, "decision": "APPROVED", "reason": "ok", "reviewer": "J"}
    assert client.post("/api/override", json=body).status_code == 401
    assert client.post("/api/override", json=body, headers={"X-Reviewer-Key": "wrong"}).status_code == 401
    assert client.post("/api/override", json=body, headers={"X-Reviewer-Key": "s3cret"}).status_code == 200


def test_unknown_ids_return_404(client):
    assert client.get("/api/requests/nope").status_code == 404
    assert client.get("/api/requests/nope/acord").status_code == 404
    assert client.post("/api/override", json={"request_id": "nope", "decision": "APPROVED",
                                              "reason": "r", "reviewer": "x"}).status_code == 404
