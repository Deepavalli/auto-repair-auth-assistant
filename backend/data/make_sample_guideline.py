"""
Generates a sample carrier-guideline PDF to exercise the ingestion pipeline.
Fabricated content. Run: python -m data.make_sample_guideline
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

TEXT = """LAKESHORE MUTUAL AUTO
Claims Guideline: Rental Reimbursement Extension

Guideline Number: GL-RENT-EXT
Repair operation: Rental vehicle extension (code AUTO-RENT-EXT)

PRE-APPROVAL REQUIRED: Yes

An extension of rental reimbursement beyond the initial authorization will be
approved when ALL of the following are met:

1. Rental reimbursement coverage is listed on the policy.

2. The insured vehicle remains at the repair facility for a covered repair,
   or is not drivable, and the delay is documented by the shop.

3. The total rental stays within the policy limit of $40 per day and
   30 days per claim.

Requests that do not meet these criteria are routed to a desk adjuster.
"""


def build(path: str = "data/sample_guideline_rental.pdf") -> None:
    c = canvas.Canvas(path, pagesize=letter)
    text = c.beginText(60, 740)
    text.setFont("Helvetica", 11)
    for line in TEXT.strip().split("\n"):
        text.textLine(line)
    c.drawText(text)
    c.save()
    print(f"wrote {path}")


if __name__ == "__main__":
    build()
