"""
Agent tests with Claude and the database mocked out - no API key or
Postgres needed. Run: pytest
"""
import agent.draft as draft_mod
import agent.evaluate as evaluate_mod
import agent.retrieve as retrieve_mod
import agent.triage as triage_mod
from agent.draft import confidence
from agent.graph import agent
from agent.llm import LLMError
from agent.state import UNTRUSTED_NOTE_RULE
from api.decisions import compute_disposition
from data.coverage_guidelines import GUIDELINES_BY_CODE
from data.sample_claims import CASE_WINDSHIELD, CASE_TOW, CASE_FRAME


def _patch_lookup(monkeypatch):
    monkeypatch.setattr(triage_mod, "find_guideline",
                        lambda service_code, carrier_name=None: GUIDELINES_BY_CODE.get(service_code))
    monkeypatch.setattr(retrieve_mod, "semantic_search", lambda q, carrier_name=None: None)


def test_confidence_weights():
    assert confidence([]) is None
    assert confidence([{"status": "met"}, {"status": "met"}]) == 1.0
    assert confidence([{"status": "met"}, {"status": "uncertain"}, {"status": "unmet"}]) == 0.5


def test_no_preapproval_short_circuits(monkeypatch):
    _patch_lookup(monkeypatch)
    called = []
    monkeypatch.setattr(evaluate_mod, "complete_json", lambda *a, **k: called.append(1))
    out = agent.invoke({"claim": CASE_TOW})
    assert out["preapproval_required"] is False
    assert "draft" not in out
    assert not called
    assert [t.split(":")[0] for t in out["trace"]] == ["extract", "triage"]


def test_full_pipeline_all_met(monkeypatch):
    _patch_lookup(monkeypatch)
    monkeypatch.setattr(evaluate_mod, "complete_json",
                        lambda *a, **k: {"status": "met", "justification": "In the note."})
    monkeypatch.setattr(draft_mod, "complete", lambda *a, **k: "Please authorize.")
    out = agent.invoke({"claim": CASE_WINDSHIELD})
    assert out["preapproval_required"] is True
    assert out["matched_guideline"].guideline_id == "GL-GLASS-RPL"
    assert len(out["criteria_checks"]) == 3
    assert out["confidence"] == 1.0
    assert compute_disposition(True, out["confidence"]) == "approved"


def test_llm_failure_becomes_uncertain(monkeypatch):
    _patch_lookup(monkeypatch)

    def boom(*a, **k):
        raise LLMError("Claude API error (OverloadedError 529)")

    monkeypatch.setattr(evaluate_mod, "complete_json", boom)
    monkeypatch.setattr(draft_mod, "complete", boom)
    out = agent.invoke({"claim": CASE_FRAME})
    assert all(c["status"] == "uncertain" for c in out["criteria_checks"])
    assert out["confidence"] == 0.5
    assert out["draft"].startswith("Draft unavailable")


def test_unknown_code_is_never_auto_approved(monkeypatch):
    """Review finding #1: no guideline -> no criteria -> must be pended, not approved."""
    _patch_lookup(monkeypatch)
    monkeypatch.setattr(draft_mod, "complete", lambda *a, **k: "draft")
    claim = CASE_WINDSHIELD.model_copy(deep=True)
    claim.repair_request.service_code = "AUTO-UNKNOWN"
    out = agent.invoke({"claim": claim})
    assert out["preapproval_required"] is True
    assert out["criteria_checks"] == []
    assert out["confidence"] is None
    assert compute_disposition(True, out["confidence"]) == "pended"


def test_prompts_carry_injection_guard(monkeypatch):
    """Review finding #6: every prompt that sees the note includes the guard."""
    import agent.appeal as appeal_mod
    for mod in (evaluate_mod, draft_mod, appeal_mod):
        assert UNTRUSTED_NOTE_RULE in mod.SYSTEM
