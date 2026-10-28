"""
FastAPI app exposing the repair-authorization agent.

  GET  /api/health
  GET  /api/guidelines                  carrier guidelines (for the UI)
  POST /api/submit?save=false          run one request through the agent (save=false: dry run)
  POST /api/batch                       run a queue of requests (per-item ok/error)
  POST /api/appeal                      draft a reconsideration letter for a stored request
  POST /api/override                    reviewer override (needs X-Reviewer-Key if REVIEWER_API_KEY is set)
  GET  /api/requests                    all processed requests, newest first
  GET  /api/requests/{id}               one request with full trace
  GET  /api/requests/{id}/acord         ACORD-inspired JSON of the decision
  GET  /api/analytics                   dashboard metrics
"""
import hmac
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api import service
from api.acord import to_acord
from api.schemas import (
    SubmitRequest, RepairAuthResult, OverrideRequest, AppealRequest, BatchItemResult,
)
from db import guideline_repo, request_repo

app = FastAPI(title="Auto Repair Authorization Assistant")

# Optional shared secret for reviewer actions. Phase 2 replaces this with real
# authentication and roles; until then it keeps anonymous users from overriding.
REVIEWER_API_KEY = os.getenv("REVIEWER_API_KEY", "")
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "50"))

origins = ["http://localhost:3000"] + [
    o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "reviewer_key_required": bool(REVIEWER_API_KEY)}


@app.get("/api/guidelines")
def guidelines():
    return [g.model_dump() for g in guideline_repo.list_all()]


@app.post("/api/submit", response_model=RepairAuthResult)
def submit(req: SubmitRequest, save: bool = True):
    return service.process_submission(req, save=save)


@app.post("/api/batch", response_model=list[BatchItemResult])
def batch(reqs: list[SubmitRequest]):
    if len(reqs) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=413, detail=f"Batch limit is {MAX_BATCH_SIZE} requests")
    # A few requests at a time; Claude concurrency is capped globally in agent/llm.py.
    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(service.process_batch_item, range(len(reqs)), reqs))


@app.post("/api/appeal")
def appeal(req: AppealRequest):
    letter = service.appeal_for(req.request_id)
    if letter is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"appeal": letter}


@app.post("/api/override", response_model=RepairAuthResult)
def override(req: OverrideRequest, x_reviewer_key: str = Header(default="")):
    if REVIEWER_API_KEY and not hmac.compare_digest(x_reviewer_key, REVIEWER_API_KEY):
        raise HTTPException(status_code=401, detail="Reviewer key required")
    result = request_repo.apply_override(req.request_id, req.decision, req.reason, req.reviewer)
    if result is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return result


@app.get("/api/requests", response_model=list[RepairAuthResult])
def list_requests():
    return request_repo.list_all()


@app.get("/api/requests/{request_id}", response_model=RepairAuthResult)
def get_request(request_id: str):
    result = request_repo.get(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return result


@app.get("/api/requests/{request_id}/acord")
def get_acord(request_id: str):
    result = request_repo.get(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return to_acord(result)


@app.get("/api/analytics")
def analytics():
    return service.analytics()
