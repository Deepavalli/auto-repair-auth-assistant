"""Guideline lookup and ingestion guards (review findings #5 and #10), on SQLite."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import db.guideline_repo as repo
import db.ingest_guideline as ingest_mod
from db.models import GuidelineRecord


@pytest.fixture
def session_factory(monkeypatch):
    engine = create_engine("sqlite://")
    GuidelineRecord.__table__.create(engine)  # embedding column is unused here
    factory = sessionmaker(bind=engine)
    with factory() as s:
        s.add(GuidelineRecord(guideline_id="GL-A", carrier_name="Lakeshore Mutual Auto",
                              service_code="AUTO-GLS-RPL", service_name="Windshield",
                              preapproval_required=True, criteria=["c1"], guideline_text="t"))
        s.commit()
    monkeypatch.setattr(repo, "SessionLocal", factory)
    monkeypatch.setattr(ingest_mod, "SessionLocal", factory)
    return factory


def test_find_guideline_matches_code_case_insensitively(session_factory):
    g = repo.find_guideline("auto-gls-rpl", "lakeshore mutual auto")
    assert g is not None and g.guideline_id == "GL-A"


def test_no_cross_carrier_fallback(session_factory):
    assert repo.find_guideline("AUTO-GLS-RPL", "Some Other Carrier") is None


def test_ingest_refuses_id_clash_without_update(session_factory, monkeypatch):
    data = {"guideline_id": "GL-A", "carrier_name": "Lakeshore Mutual Auto",
            "service_code": "AUTO-NEW", "service_name": "New", "preapproval_required": True,
            "criteria": ["x"]}
    monkeypatch.setattr(ingest_mod, "extract_text", lambda p: "pdf text")
    monkeypatch.setattr(ingest_mod, "complete_json", lambda *a, **k: dict(data))
    monkeypatch.setattr(ingest_mod, "available", lambda: False)
    with pytest.raises(ingest_mod.GuidelineExistsError):
        ingest_mod.ingest("x.pdf")
    assert ingest_mod.ingest("x.pdf", update=True) == "GL-A"
    assert repo.find_guideline("AUTO-NEW", "Lakeshore Mutual Auto").guideline_id == "GL-A"
