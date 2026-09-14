"""tc_convergence — the Convergence Engine (Part VIII, §36–§39, §150).

An opportunity is stronger when genuinely INDEPENDENT evidence domains agree
(TC-ADR-013). This engine does NOT count indicators (§36): it groups evidence into
factor families (ConvergenceDomain), collapses correlated evidence so it is not
double-counted (§39, TC-ADR-028), applies an independence + freshness + source-
confidence + regime-relevance adjustment (§150), and produces a 0–100 score that
RETAINS its components — the score never replaces explainability (§38).
"""

from tc_convergence.engine import (
    ConvergenceResult,
    DomainInput,
    score_convergence,
)

__all__ = ["ConvergenceResult", "DomainInput", "score_convergence"]
