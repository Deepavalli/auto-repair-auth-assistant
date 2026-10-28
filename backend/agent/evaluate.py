"""
Node 4: Evaluate (Claude).

For each guideline criterion, asks Claude whether the claim file satisfies
it: met / unmet / uncertain, plus a one-sentence justification. Uses
structured outputs so the answer is always valid JSON, and checks the
criteria in parallel to keep latency low.
"""
from concurrent.futures import ThreadPoolExecutor

from agent.state import AgentState, log, UNTRUSTED_NOTE_RULE
from agent.llm import complete_json, LLMError

SYSTEM = (
    "You are an experienced auto insurance claims reviewer. You judge strictly from the "
    "evidence in the claim file. If the file does not clearly show a criterion is met, "
    "answer 'uncertain' (missing information) or 'unmet' (evidence contradicts it)."
    + " " + UNTRUSTED_NOTE_RULE
)

PROMPT = """Decide whether this claim file satisfies ONE carrier guideline criterion.

<claim_facts>
{facts}
</claim_facts>

<adjuster_note>
{note}
</adjuster_note>

<criterion>
{criterion}
</criterion>

Return status as one of: met, unmet, uncertain.
Return justification as one sentence citing the specific fact from the claim file."""

SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["met", "unmet", "uncertain"]},
        "justification": {"type": "string"},
    },
    "required": ["status", "justification"],
    "additionalProperties": False,
}


def check_criterion(claim, criterion: str) -> dict:
    try:
        out = complete_json(
            PROMPT.format(facts=claim.facts(), note=claim.note_text, criterion=criterion),
            schema=SCHEMA,
            system=SYSTEM,
        )
        status = str(out.get("status", "uncertain")).lower()
        if status not in ("met", "unmet", "uncertain"):
            status = "uncertain"
        return {"criterion": criterion, "status": status,
                "justification": out.get("justification", "")}
    except LLMError as exc:
        return {"criterion": criterion, "status": "uncertain",
                "justification": f"Automatic review failed ({exc}); needs manual review."}


def evaluate_node(state: AgentState) -> AgentState:
    guideline = state.get("matched_guideline")
    if guideline is None or not guideline.criteria:
        state["criteria_checks"] = []
        log(state, "evaluate: no criteria to check")
        return state

    claim = state["claim"]
    with ThreadPoolExecutor(max_workers=min(4, len(guideline.criteria))) as pool:
        checks = list(pool.map(lambda c: check_criterion(claim, c), guideline.criteria))

    state["criteria_checks"] = checks
    met = sum(1 for c in checks if c["status"] == "met")
    log(state, f"evaluate: {met}/{len(checks)} criteria met")
    return state
