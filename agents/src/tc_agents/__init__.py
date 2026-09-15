"""tc_agents — specialist intelligence agents (Part XIV, §58-§66).

Each specialist answers ONE narrow question and returns a structured
:class:`Assessment` — never an order, never a size, never a risk override (§55,
TC-ADR-012). They are deliberately THIN: the numeric work already lives in the
deterministic engines (quant, convergence, macro, portfolio), and a specialist's job is
to interpret that output into a domain opinion with a rationale.

That thinness is the point. A fat agent that recomputes indicators would duplicate
(and eventually contradict) the engines. Register-first: specialists defer to engines.

Specialists implemented (§58-66):
    regime, trend, momentum, structure, volatility, macro, event-intelligence,
    market-leaders, portfolio
The adversarial critic (§67) is separate and already lives in tc_decision.
"""

from tc_agents.base import Assessment, Specialist
from tc_agents.specialists import (
    EventIntelligenceSpecialist,
    MacroSpecialist,
    MarketLeadersSpecialist,
    MomentumSpecialist,
    PortfolioSpecialist,
    RegimeSpecialist,
    StructureSpecialist,
    TrendSpecialist,
    VolatilitySpecialist,
    all_specialists,
)

__all__ = [
    "Assessment",
    "Specialist",
    "RegimeSpecialist",
    "TrendSpecialist",
    "MomentumSpecialist",
    "StructureSpecialist",
    "VolatilitySpecialist",
    "MacroSpecialist",
    "EventIntelligenceSpecialist",
    "MarketLeadersSpecialist",
    "PortfolioSpecialist",
    "all_specialists",
]
