"""
Node 1: Extract.

Pulls the facts the rest of the agent needs out of the claim file - mainly
the requested repair-operation code. Submissions already carry a structured
RepairRequest, so this node lifts it into state. For free-text-only
submissions this is the place to add a Claude extraction call.
"""
from agent.state import AgentState, log


def extract_node(state: AgentState) -> AgentState:
    req = state["claim"].repair_request
    state["service_code"] = req.service_code.strip().upper()
    log(state, f"extract: identified requested repair {state['service_code']} ({req.service_name})")
    return state
