"""
CLI runner: watch the agent work on a synthetic claim (no API/UI needed,
but needs the database seeded and ANTHROPIC_API_KEY set).

  python run_agent.py windshield | frame | tow | adas | all
"""
import sys

from agent.graph import agent
from data.sample_claims import ALL_CASES


def run_case(key: str) -> None:
    claim = ALL_CASES[key]
    print(f"\n{'=' * 70}\nCASE: {key}  ({claim.repair_request.service_name})\n{'=' * 70}")
    result = agent.invoke({"claim": claim})

    print("\n--- TRACE ---")
    for line in result.get("trace", []):
        print("  ", line)
    print("\n--- OUTCOME ---")
    print("  Pre-approval required:", result.get("preapproval_required"))
    for c in result.get("criteria_checks", []):
        print(f"    [{c['status']}] {c['criterion']}\n        -> {c['justification']}")
    if result.get("draft"):
        print("\n--- DRAFT ---\n" + result["draft"])
        print("\n  Confidence:", result.get("confidence"))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "windshield"
    for key in (ALL_CASES if arg == "all" else [arg]):
        run_case(key)
