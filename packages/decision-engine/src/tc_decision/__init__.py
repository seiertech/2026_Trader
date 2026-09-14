"""tc_decision — the Decision Engine (Part XV, §68–§70).

Consumes an opportunity plus its evidence, the regime, the critic verdict and the risk
gate result, and produces an immutable :class:`Decision` (§90, TC-ADR-018) with one of
LONG / SHORT / WAIT / REJECT (§69). WAIT is a first-class state — the opportunity may
be reassessed later (§70).

The engine is deterministic and orchestrates existing deterministic components; it
does NOT invent market facts and it does NOT override risk (§55, §73). Every decision
is explainable in plain English AND detailed evidence (§101).
"""

from tc_decision.critic import CriticInputs, criticise
from tc_decision.engine import DecisionInputs, decide

__all__ = ["DecisionInputs", "decide", "CriticInputs", "criticise"]
