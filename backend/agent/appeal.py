"""
Reconsideration (appeal / supplement) letter, drafted by Claude.

Used when a request is likely to be denied or pended. It works from the
STORED result (criteria already evaluated), so it does not re-run the agent.
"""
from agent.llm import complete
from agent.state import UNTRUSTED_NOTE_RULE

SYSTEM = (
    "You write reconsideration requests from auto body shops to insurance carriers. "
    "Be respectful and factual; acknowledge gaps honestly and never invent facts."
    + " " + UNTRUSTED_NOTE_RULE
)

PROMPT = """Write a reconsideration request (one or two short paragraphs) for this repair.
- Lean on the criteria that ARE met, citing specific facts.
- Acknowledge unmet or uncertain criteria honestly and state what documentation will be supplied.

Policyholder: {policyholder}
Carrier: {carrier}
Vehicle: {vehicle}
Requested repair: {service} ({code}), estimate {estimate}

<criteria_results>
{criteria}
</criteria_results>

<adjuster_note>
{note}
</adjuster_note>"""


def draft_appeal(result) -> str:
    """`result` is an api.schemas.RepairAuthResult."""
    criteria = "\n".join(
        f"- [{c.status.upper()}] {c.criterion} -> {c.justification}" for c in result.criteria
    ) or "No specific criteria applied."
    estimate = f"${result.estimated_cost:,.2f}" if result.estimated_cost is not None else "not provided"
    return complete(
        PROMPT.format(
            policyholder=result.policyholder_name,
            carrier=result.carrier_name or "the carrier",
            vehicle=result.vehicle or "not provided",
            service=result.service_name,
            code=result.service_code,
            estimate=estimate,
            criteria=criteria,
            note=result.note_text,
        ),
        system=SYSTEM,
    )
