"""tc_permissions — market permission state machine (§133, §153, TC-ADR-026).

Observation NEVER implies authority to trade (§133). Every instrument carries a
permission state, and promotion between states requires configuration change, evidence
and an ADR — it is never automatic and never inferred from good results.

    INTELLIGENCE_ONLY  → SHADOW_TRADABLE → LIVE_TRADABLE
                       ↘ PROHIBITED (terminal)

Hard rules enforced here:
  * crypto is ALWAYS PROHIBITED and can never be promoted (§7, TC-ADR-006);
  * promotion to LIVE_TRADABLE additionally requires proof-of-edge evidence and an ADR
    reference (§75 promotion gates) — profit and schedule are NOT valid grounds (§0);
  * demotion is always allowed (fail closed / safe direction).
"""

from tc_permissions.engine import (
    PermissionDecision,
    PermissionEngine,
    PromotionRequest,
)

__all__ = ["PermissionEngine", "PromotionRequest", "PermissionDecision"]
