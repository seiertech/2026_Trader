"""tc_leaders — Market Leaders intelligence (§19, §148).

Market-leading companies are grouped into configurable intelligence baskets (§19).
The critical rule (§148, TC-ADR-028): when constituents of a basket move together,
that is ONE derived factor, not N independent signals — otherwise NVIDIA↓ AMD↓
Broadcom↓ would triple-count what is really "semiconductor weakness" (§39).

This engine computes a single basket factor from constituent moves (magnitude +
directional coherence), and emits it as a CORPORATE_SECTOR convergence DomainInput
tagged with a correlation_group so the Convergence Engine collapses it correctly.
Companies are intelligence inputs, NOT tradable in V1 (§6, TC-ADR-008).
"""

from tc_leaders.baskets import (
    Basket,
    BasketFactor,
    ConstituentMove,
    basket_convergence_input,
    basket_factor,
)
from tc_leaders.seed import load_baskets_from_config

__all__ = [
    "Basket",
    "BasketFactor",
    "ConstituentMove",
    "basket_factor",
    "basket_convergence_input",
    "load_baskets_from_config",
]
