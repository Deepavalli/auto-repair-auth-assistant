"""
Node 5: Draft (Claude).

Writes the repair-authorization request the shop sends to the carrier, and
computes a confidence score: met = 1, uncertain = 0.5, unmet = 0, averaged.
When no guideline was found there are no criteria, so confidence is None and
the request is routed to an adjuster (never auto-approved).
"""
from agent.state import AgentState, log, UNTRUSTED_NOTE_RULE
from agent.llm import complete, LLMError

SYSTEM = (
    "You write repair-authorization requests from auto body shops to insurance carriers. "
    "Be concise, professional and factual. Never invent facts that are not in the claim file."
    + " " + UNTRUSTED_NOTE_RULE
)

PROMPT = """Write one short paragraph requesting carrier authorization for the repair below.
Reference the specific facts that satisfy each guideline criterion. If any criterion is
unmet or uncertain, say plainly what documentation will follow.

<claim_facts>
{facts}
</claim_facts>

<guideline>{guideline}</guideline>

<criteria_results>
{criteria}
</criteria_results>

<adjuster_note>
{note}
</adjuster_note>"""

WEIGHTS = {"met": 1.0, "uncertain": 0.5, "unmet": 0.0}


def confidence(checks: list[dict]) -> float | None:
    """Average of criterion weights. None when there is nothing to score."""
    if not checks:
        return None
    return round(sum(WEIGHTS.get(c["status"], 0.5) for c in checks) / len(checks), 2)


def summarize(checks: list[dict]) -> str:
    return "\n".join(
        f"- [{c['status'].upper()}] {c['criterion']} -> {c['justification']}" for c in checks
    ) or "No specific criteria applied."


def draft_node(state: AgentState) -> AgentState:
    claim = state["claim"]
    guideline = state.get("matched_guideline")
    checks = state.get("criteria_checks", [])
    try:
        state["draft"] = complete(
            PROMPT.format(
                facts=claim.facts(),
                guideline=guideline.guideline_id if guideline else "none found",
                criteria=summarize(checks),
                note=claim.note_text,
            ),
            system=SYSTEM,
        )
    except LLMError as exc:
        state["draft"] = f"Draft unavailable: {exc}"
    state["confidence"] = confidence(checks)
    if guideline is None:
        log(state, "draft: no guideline found; request drafted for adjuster review")
    else:
        log(state, f"draft: authorization request drafted, confidence {state['confidence']}")
    return state
