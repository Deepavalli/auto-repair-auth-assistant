"""
Node 2: Triage.

Decides whether the carrier requires pre-approval for this repair by looking
up the governing guideline by code (and carrier). If no pre-approval is
needed, the graph short-circuits and skips retrieve/evaluate/draft.
Unknown codes default to "pre-approval required" - the safe choice.
"""
from agent.state import AgentState, log
from db.guideline_repo import find_guideline


def triage_node(state: AgentState) -> AgentState:
    claim = state["claim"]
    code = state["service_code"]
    guideline = find_guideline(service_code=code, carrier_name=claim.policy.carrier_name)

    if guideline is None:
        state["preapproval_required"] = True
        state["matched_guideline"] = None
        log(state, f"triage: no guideline for {code} from carrier "
                   f"'{claim.policy.carrier_name}'; defaulting to pre-approval required")
        return state

    state["preapproval_required"] = guideline.preapproval_required
    state["matched_guideline"] = guideline
    log(state, f"triage: guideline {guideline.guideline_id} says pre-approval "
               f"{'required' if guideline.preapproval_required else 'NOT required'}")
    return state
