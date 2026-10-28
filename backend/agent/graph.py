"""
The repair-authorization agent, assembled from five nodes:

    extract -> triage -> (branch)
        pre-approval required:  retrieve -> evaluate -> draft -> END
        not required:           END
"""
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.extract import extract_node
from agent.triage import triage_node
from agent.retrieve import retrieve_node
from agent.evaluate import evaluate_node
from agent.draft import draft_node


def _needs_preapproval(state: AgentState) -> str:
    return "retrieve" if state.get("preapproval_required") else "end"


def build_agent():
    g = StateGraph(AgentState)
    g.add_node("extract_step", extract_node)
    g.add_node("triage_step", triage_node)
    g.add_node("retrieve_step", retrieve_node)
    g.add_node("evaluate_step", evaluate_node)
    g.add_node("draft_step", draft_node)

    g.set_entry_point("extract_step")
    g.add_edge("extract_step", "triage_step")
    g.add_conditional_edges("triage_step", _needs_preapproval,
                            {"retrieve": "retrieve_step", "end": END})
    g.add_edge("retrieve_step", "evaluate_step")
    g.add_edge("evaluate_step", "draft_step")
    g.add_edge("draft_step", END)
    return g.compile()


agent = build_agent()
