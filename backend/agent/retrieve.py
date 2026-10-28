"""
Node 3: Retrieve.

Confirms the governing guideline. If triage found one by exact code it is
reused; otherwise we try semantic search over guideline embeddings
(pgvector), when ENABLE_SEMANTIC_SEARCH=true.
"""
from agent.state import AgentState, log
from db.guideline_repo import semantic_search


def retrieve_node(state: AgentState) -> AgentState:
    guideline = state.get("matched_guideline")
    if guideline is not None:
        log(state, f"retrieve: using guideline {guideline.guideline_id} "
                   f"({guideline.carrier_name}) via code match, {len(guideline.criteria)} criteria")
        return state

    claim = state["claim"]
    query = f"{claim.repair_request.service_name}. {claim.note_text}"
    guideline = semantic_search(query, carrier_name=claim.policy.carrier_name)
    state["matched_guideline"] = guideline
    if guideline is not None:
        log(state, f"retrieve: matched guideline {guideline.guideline_id} via semantic search")
    else:
        log(state, f"retrieve: no guideline found for {state['service_code']}")
    return state
