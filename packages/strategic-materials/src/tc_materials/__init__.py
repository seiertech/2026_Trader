"""tc_materials — Strategic Materials intelligence (§137-138, TC-ADR-023).

A first-class intelligence domain. The taxonomy (§137) covers precious, industrial,
battery, semiconductor and rare-earth materials plus energy materials.

The methodology matters (§138): the system models DEMAND/SUPPLY TRANSMISSION, not
material price momentum. A gallium export restriction is interesting because of what it
does to component supply → semiconductors → tech leaders → indices, not because gallium
"went up". Transmission chains are explicit, config-driven, and resolve through the
relationship graph to tradable instruments.

Most materials have no liquid broker instrument and therefore stay INTELLIGENCE_ONLY
(§137, §133) — that permission decision is the permissions engine's, not this module's.
"""

from tc_materials.materials import (
    MATERIAL_TAXONOMY,
    TRANSMISSION_CHAINS,
    MaterialClass,
    SupplyShock,
    chain_for,
    materials_convergence_input,
)

__all__ = [
    "MaterialClass",
    "MATERIAL_TAXONOMY",
    "TRANSMISSION_CHAINS",
    "SupplyShock",
    "chain_for",
    "materials_convergence_input",
]
