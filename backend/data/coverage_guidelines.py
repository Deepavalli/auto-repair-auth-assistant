"""
Synthetic carrier repair-authorization guidelines.

Fabricated but structured like real auto-claims guidelines: each names a
repair operation, states whether the carrier requires pre-approval before
the shop starts work, and lists the criteria that must be met. The agent
retrieves the relevant guideline and checks the claim against it.

Kept separate from the agent so real guidelines (e.g. ingested PDFs) can
replace these without touching agent logic.
"""
from pydantic import BaseModel, Field

CARRIER = "Lakeshore Mutual Auto"


class CoverageGuideline(BaseModel):
    guideline_id: str
    carrier_name: str
    service_code: str = Field(description="Repair-operation code this guideline governs")
    service_name: str
    preapproval_required: bool
    criteria: list[str] = Field(default_factory=list)
    guideline_text: str = Field(description="Full narrative, used for retrieval")


GUIDELINES: list[CoverageGuideline] = [
    CoverageGuideline(
        guideline_id="GL-GLASS-RPL",
        carrier_name=CARRIER,
        service_code="AUTO-GLS-RPL",
        service_name="Windshield replacement",
        preapproval_required=True,
        criteria=[
            "Comprehensive (or full glass) coverage is active on the date of loss",
            "Damage cannot be fixed by a resin chip repair: a crack longer than 6 inches "
            "or damage inside the driver's critical viewing area",
            "Damage is documented with photos or a written inspection note",
        ],
        guideline_text=(
            "Windshield replacement (AUTO-GLS-RPL) requires carrier pre-approval. "
            "Replacement is authorized when comprehensive or full glass coverage is in "
            "force on the date of loss, the damage cannot be repaired with a resin chip "
            "repair because the crack exceeds 6 inches or lies in the driver's critical "
            "viewing area, and the damage is documented with photos or an inspection note."
        ),
    ),
    CoverageGuideline(
        guideline_id="GL-ADAS-CAL",
        carrier_name=CARRIER,
        service_code="AUTO-ADAS-CAL",
        service_name="ADAS camera/sensor recalibration",
        preapproval_required=True,
        criteria=[
            "Vehicle is equipped with advanced driver-assistance systems (e.g. lane-keep "
            "camera, radar cruise control)",
            "Recalibration is required because of a covered repair (windshield, bumper, "
            "grille or mirror replacement)",
            "Calibration will follow the manufacturer (OEM) procedure with pre- and "
            "post-repair scan reports",
        ],
        guideline_text=(
            "ADAS recalibration (AUTO-ADAS-CAL) requires pre-approval. It is covered when "
            "the vehicle has driver-assistance cameras or sensors, a covered repair such as "
            "windshield or bumper replacement makes recalibration necessary, and the shop "
            "follows the OEM calibration procedure with pre- and post-repair scans."
        ),
    ),
    CoverageGuideline(
        guideline_id="GL-STR-FRM",
        carrier_name=CARRIER,
        service_code="AUTO-STR-FRM",
        service_name="Structural / frame repair",
        preapproval_required=True,
        criteria=[
            "Collision coverage is active on the date of loss",
            "Structural damage is documented with a frame measurement report",
            "Estimated repair cost is below 75 percent of the vehicle's actual cash value "
            "(otherwise the claim is evaluated as a potential total loss)",
        ],
        guideline_text=(
            "Structural and frame repair (AUTO-STR-FRM) requires pre-approval. Repairs are "
            "authorized when collision coverage is in force, structural damage is supported "
            "by a frame measurement report, and the estimate is below 75 percent of the "
            "vehicle's actual cash value; above that threshold the vehicle is reviewed as a "
            "potential total loss."
        ),
    ),
    CoverageGuideline(
        guideline_id="GL-TOW-STD",
        carrier_name=CARRIER,
        service_code="AUTO-TOW-STD",
        service_name="Standard tow to repair facility",
        preapproval_required=False,
        criteria=[],
        guideline_text=(
            "A standard tow (AUTO-TOW-STD) to the nearest qualified repair facility does not "
            "require pre-approval when towing coverage is on the policy."
        ),
    ),
]

GUIDELINES_BY_CODE = {g.service_code: g for g in GUIDELINES}
