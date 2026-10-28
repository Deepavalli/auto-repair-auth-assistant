"""
Single source of truth for the business decision shown to users.

  overridden by a reviewer   -> "approved" / "denied" (reviewer's call)
  no pre-approval needed     -> "no-preapproval-required"
  all criteria met (1.0)     -> "approved"  (recommend approval)
  anything else              -> "pended"    (adjuster review needed), including
                                no guideline found (confidence None)
"""
from typing import Optional

APPROVED = "approved"
DENIED = "denied"
PENDED = "pended"
NOT_REQUIRED = "no-preapproval-required"


def compute_disposition(preapproval_required: bool, confidence: Optional[float],
                        overridden: bool = False, override_decision: Optional[str] = None) -> str:
    if overridden and override_decision:
        return override_decision.lower()
    if not preapproval_required:
        return NOT_REQUIRED
    if confidence is not None and confidence >= 1.0:
        return APPROVED
    return PENDED
