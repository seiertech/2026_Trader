"""Material taxonomy, supply shocks and transmission chains (§137-138)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tc_domain.enums import ConvergenceDomain, ImpactDirection


class MaterialClass(StrEnum):
    PRECIOUS = "PRECIOUS"
    INDUSTRIAL = "INDUSTRIAL"
    BATTERY = "BATTERY"
    SEMICONDUCTOR = "SEMICONDUCTOR"
    RARE_EARTHS = "RARE_EARTHS"
    ENERGY_MATERIALS = "ENERGY_MATERIALS"


# §137 taxonomy, verbatim.
MATERIAL_TAXONOMY: dict[MaterialClass, tuple[str, ...]] = {
    MaterialClass.PRECIOUS: ("GOLD", "SILVER", "PLATINUM", "PALLADIUM"),
    MaterialClass.INDUSTRIAL: ("COPPER", "ALUMINIUM", "NICKEL", "ZINC"),
    MaterialClass.BATTERY: ("LITHIUM", "NICKEL", "COBALT", "GRAPHITE", "MANGANESE"),
    MaterialClass.SEMICONDUCTOR: ("GALLIUM", "GERMANIUM", "SILICON"),
    MaterialClass.RARE_EARTHS: ("NEODYMIUM", "DYSPROSIUM", "PRASEODYMIUM"),
    MaterialClass.ENERGY_MATERIALS: ("URANIUM",),
}

# §138 transmission chains: material -> ordered path of affected links. These are
# HYPOTHESIS paths (§32) — they say what COULD transmit, never that a trade is warranted.
TRANSMISSION_CHAINS: dict[str, tuple[str, ...]] = {
    "COPPER": ("AI_CAPEX", "DATA_CENTRES", "POWER_DEMAND", "GRID_EXPANSION",
               "COPPER", "INDUSTRIALS", "EQUITY_INDICES"),
    "URANIUM": ("POWER_DEMAND", "NUCLEAR_RENAISSANCE", "URANIUM", "UTILITIES",
                "EQUITY_INDICES"),
    "SILVER": ("AI_CAPEX", "POWER_DEMAND", "SILVER", "INDUSTRIALS", "EQUITY_INDICES"),
    "LITHIUM": ("LITHIUM", "BATTERY_COST_AND_SUPPLY", "EV_PRODUCTION",
                "AUTOMOTIVE_SECTOR", "REGIONAL_INDICES"),
    "COBALT": ("COBALT", "BATTERY_COST_AND_SUPPLY", "EV_PRODUCTION",
               "AUTOMOTIVE_SECTOR", "REGIONAL_INDICES"),
    "GRAPHITE": ("GRAPHITE", "BATTERY_COST_AND_SUPPLY", "EV_PRODUCTION",
                 "AUTOMOTIVE_SECTOR", "REGIONAL_INDICES"),
    "GALLIUM": ("GALLIUM", "COMPONENT_SUPPLY_RISK", "SEMICONDUCTORS",
                "AI_INFRASTRUCTURE", "TECHNOLOGY", "NAS100"),
    "GERMANIUM": ("GERMANIUM", "COMPONENT_SUPPLY_RISK", "SEMICONDUCTORS",
                  "AI_INFRASTRUCTURE", "TECHNOLOGY", "NAS100"),
    "NEODYMIUM": ("NEODYMIUM", "COMPONENT_SUPPLY_RISK", "SEMICONDUCTORS",
                  "TECHNOLOGY", "NAS100"),
}


def class_of(material: str) -> MaterialClass | None:
    m = material.upper()
    for cls, members in MATERIAL_TAXONOMY.items():
        if m in members:
            return cls
    return None


def chain_for(material: str) -> tuple[str, ...]:
    """The §138 transmission path for a material (empty if none modelled)."""
    return TRANSMISSION_CHAINS.get(material.upper(), ())


@dataclass(frozen=True)
class SupplyShock:
    """A supply/demand disruption in a material (§138)."""

    material: str
    # +1 = supply RESTRICTED (scarcer, upward price/downstream cost pressure)
    # -1 = supply EASED / demand collapse
    direction: int
    severity: float          # 0..1
    source_count: int = 1
    detail: str = ""

    @property
    def material_class(self) -> MaterialClass | None:
        return class_of(self.material)


def materials_convergence_input(
    shock: SupplyShock,
    *,
    downstream_is_cost_pressured: bool = True,
    freshness: float = 1.0,
):
    """Adapt a supply shock to a STRATEGIC_MATERIALS_SUPPLY_CHAIN convergence input (§150).

    Direction is about the DOWNSTREAM instrument, not the material: a supply restriction
    raises input costs for manufacturers, which is BEARISH for the downstream equity
    expression even though the material itself gets dearer. ``downstream_is_cost_pressured``
    lets the caller flip that when the tradable expression is the material/producer
    itself (e.g. gold, or a miner), where scarcity is bullish.
    """
    from tc_convergence import DomainInput

    restricted = shock.direction >= 0
    if downstream_is_cost_pressured:
        direction = ImpactDirection.BEARISH if restricted else ImpactDirection.BULLISH
    else:
        direction = ImpactDirection.BULLISH if restricted else ImpactDirection.BEARISH

    # Corroboration tempers severity — one report is a rumour (§29).
    corroboration = min(1.0, shock.source_count / 3.0)
    strength = round(min(100.0, shock.severity * 100.0 * corroboration), 2)
    path = " → ".join(chain_for(shock.material)) or shock.material

    return DomainInput(
        domain=ConvergenceDomain.STRATEGIC_MATERIALS_SUPPLY_CHAIN,
        strength=strength,
        direction=direction,
        rationale=(
            f"{shock.material} supply {'restricted' if restricted else 'eased'} "
            f"(severity {shock.severity:.2f}, {shock.source_count} src): {path}"
        ),
        freshness=freshness,
        # One material shock is ONE factor however many downstream links it touches (§39).
        correlation_group=f"material:{shock.material.upper()}",
    )
