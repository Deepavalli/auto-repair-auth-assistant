"""
Carrier-guideline ingestion pipeline:

  PDF -> extract text (pypdf) -> Claude structures it (structured outputs)
      -> embed (optional) -> upsert into the guidelines table

The agent reads from the same table, so an ingested guideline is usable
immediately with no code changes.

Run: python -m db.ingest_guideline data/sample_guideline_rental.pdf
     python -m db.ingest_guideline <pdf> --update     # allow replacing an existing id

Because Claude reads the guideline id from the PDF (or invents one), an id
clash is refused by default so an ingest can never silently overwrite an
existing guideline.
"""
import argparse

from pypdf import PdfReader

from agent.llm import complete_json
from db.database import SessionLocal
from db.embeddings import available, embed
from db.models import GuidelineRecord

PROMPT = """Extract this auto-insurance carrier claims guideline into structured fields.
If no guideline number is present, create a short id starting with GL-.

<guideline>
{text}
</guideline>"""

SCHEMA = {
    "type": "object",
    "properties": {
        "guideline_id": {"type": "string"},
        "carrier_name": {"type": "string"},
        "service_code": {"type": "string"},
        "service_name": {"type": "string"},
        "preapproval_required": {"type": "boolean"},
        "criteria": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["guideline_id", "carrier_name", "service_code", "service_name",
                 "preapproval_required", "criteria"],
    "additionalProperties": False,
}


def extract_text(pdf_path: str) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)


class GuidelineExistsError(RuntimeError):
    pass


def ingest(pdf_path: str, update: bool = False) -> str:
    print(f"reading {pdf_path}")
    text = extract_text(pdf_path)

    print("structuring with Claude...")
    data = complete_json(PROMPT.format(text=text), schema=SCHEMA)
    print(f"  -> {data['service_code']} ({data['service_name']}), {len(data['criteria'])} criteria")

    embedding = embed(text) if available() else None

    with SessionLocal() as session:
        rec = session.get(GuidelineRecord, data["guideline_id"])
        if rec is not None and not update:
            raise GuidelineExistsError(
                f"Guideline {data['guideline_id']} already exists "
                f"({rec.service_code} for {rec.carrier_name}). Re-run with --update to replace it."
            )
        action = "updated" if rec else "inserted"
        if rec is None:
            rec = GuidelineRecord(guideline_id=data["guideline_id"])
            session.add(rec)
        rec.carrier_name = data["carrier_name"]
        rec.service_code = data["service_code"].upper()
        rec.service_name = data["service_name"]
        rec.preapproval_required = data["preapproval_required"]
        rec.criteria = data["criteria"]
        rec.guideline_text = text
        rec.embedding = embedding
        session.commit()

    print(f"{action} guideline {data['guideline_id']}")
    return data["guideline_id"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a carrier guideline PDF")
    parser.add_argument("pdf", nargs="?", default="data/sample_guideline_rental.pdf")
    parser.add_argument("--update", action="store_true", help="replace an existing guideline id")
    args = parser.parse_args()
    try:
        ingest(args.pdf, update=args.update)
    except GuidelineExistsError as exc:
        raise SystemExit(str(exc))
