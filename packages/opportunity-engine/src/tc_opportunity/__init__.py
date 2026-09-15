"""tc_opportunity — the Opportunity Engine (Part IX, §40-42, §151).

Formalises the opportunity lifecycle that was previously inline in the runtime:

  detect (origin MARKET | EVENT | CONVERGENCE, §40)
    → live (until expiry, §42)
    → reassess (WAIT is first-class, §70 — a new assessment, not an edit §90)
    → expire / resolve

Every opportunity has an expiry and stale ones are REJECTED (§42). Reassessment
creates a new record rather than mutating the original (§90, TC-ADR-018).
"""

from tc_opportunity.engine import OpportunityEngine, OpportunityRecord

__all__ = ["OpportunityEngine", "OpportunityRecord"]
