"""Strategic materials (§137-138), healthcare (§139-143), supply chain (§144),
cross-market (§149, TC-ADR-030)."""

from __future__ import annotations

from tc_crossmarket import CrossMarketCandidate, cleanest_expression, rank_expressions
from tc_crossmarket.propagation import PROPAGATION_PATHS, crossmarket_convergence_input
from tc_domain.enums import ConvergenceDomain, ImpactDirection, MarketPermission
from tc_graph import load_graph_from_config
from tc_healthcare import HealthcareEvent, healthcare_convergence_input, issuer_impact
from tc_materials import MATERIAL_TAXONOMY, MaterialClass, SupplyShock, chain_for
from tc_materials.materials import materials_convergence_input
from tc_supply import SupplyChain, add_chain_to_graph, chain_edges

# --- strategic materials (§137-138) ---

def test_taxonomy_covers_spec_classes() -> None:
    assert "GOLD" in MATERIAL_TAXONOMY[MaterialClass.PRECIOUS]
    assert "GALLIUM" in MATERIAL_TAXONOMY[MaterialClass.SEMICONDUCTOR]
    assert "URANIUM" in MATERIAL_TAXONOMY[MaterialClass.ENERGY_MATERIALS]


def test_transmission_chain_is_modelled_not_momentum() -> None:
    chain = chain_for("GALLIUM")
    # §138: the chain, not the material price, is the intelligence.
    assert "COMPONENT_SUPPLY_RISK" in chain
    assert chain[-1] == "NAS100"


def test_supply_restriction_is_bearish_downstream() -> None:
    s = SupplyShock("GALLIUM", direction=+1, severity=0.8, source_count=3)
    di = materials_convergence_input(s, downstream_is_cost_pressured=True)
    # Input costs rise => bearish for the downstream manufacturer expression.
    assert di.direction is ImpactDirection.BEARISH
    assert di.domain is ConvergenceDomain.STRATEGIC_MATERIALS_SUPPLY_CHAIN


def test_supply_restriction_is_bullish_for_the_material_itself() -> None:
    s = SupplyShock("GOLD", direction=+1, severity=0.8, source_count=3)
    di = materials_convergence_input(s, downstream_is_cost_pressured=False)
    assert di.direction is ImpactDirection.BULLISH


def test_single_source_shock_is_tempered() -> None:
    one = materials_convergence_input(SupplyShock("COPPER", 1, 1.0, source_count=1))
    many = materials_convergence_input(SupplyShock("COPPER", 1, 1.0, source_count=3))
    assert one.strength < many.strength  # a lone report is a rumour (§29)


def test_material_shock_is_one_factor() -> None:
    di = materials_convergence_input(SupplyShock("COPPER", 1, 0.5, 3))
    assert di.correlation_group == "material:COPPER"


# --- healthcare (§140-143) ---

def test_issuer_impact_polarity() -> None:
    assert issuer_impact("DRUG_APPROVAL") > 0
    assert issuer_impact("TRIAL_HALT") < 0
    assert issuer_impact("CLINICAL_TRIAL_RESULT") == 0  # depends on the result


def test_authority_sources_outrank_general_news() -> None:
    reg = HealthcareEvent("DRUG_APPROVAL", company="Pfizer", sources=("FDA",))
    news = HealthcareEvent("DRUG_APPROVAL", company="Pfizer", sources=("BlogX",))
    assert reg.authority_weight > news.authority_weight  # §141


def test_higher_order_effects_carry_lower_confidence() -> None:
    first = HealthcareEvent("DRUG_APPROVAL", company="Lilly", sources=("FDA",),
                            severity=1.0, order=1)
    third = HealthcareEvent("DRUG_APPROVAL", company="Lilly", sources=("FDA",),
                            severity=1.0, order=3)
    a, c = healthcare_convergence_input(first), healthcare_convergence_input(third)
    assert a.strength > c.strength  # §143


def test_ambiguous_event_is_uncertain_not_guessed() -> None:
    ev = HealthcareEvent("CLINICAL_TRIAL_RESULT", company="X", sources=("EMA",))
    assert healthcare_convergence_input(ev).direction is ImpactDirection.UNCERTAIN


def test_impact_override_respected() -> None:
    ev = HealthcareEvent("CLINICAL_TRIAL_RESULT", company="X", sources=("EMA",),
                         impact_override=+1)
    assert healthcare_convergence_input(ev).direction is ImpactDirection.BULLISH


# --- supply chain (§144) ---

def test_chain_edges_follow_flow_of_goods() -> None:
    c = SupplyChain("evc", ("LITHIUM", "BATTERY", "EV_MAKER", "AUTOS", "DAX"),
                    terminal_instrument="DAX")
    edges = chain_edges(c)
    assert len(edges) == 4
    assert edges[0][0] == "LITHIUM" and edges[0][1] == "BATTERY"


def test_chain_added_to_graph_and_propagates() -> None:
    g = load_graph_from_config("config/relationships.yaml")
    c = SupplyChain("gallium_chain",
                    ("GALLIUM", "COMPONENT_SUPPLY_RISK", "SEMICONDUCTORS"),
                    terminal_instrument=None)
    added = add_chain_to_graph(c, g)
    assert added == 2
    # GALLIUM now reaches NAS100 through the pre-seeded semis->tech->NAS100 path (§22).
    reached = {h.instrument for h in g.propagate("GALLIUM", max_depth=5)}
    assert "NAS100" in reached


def test_existing_entity_type_not_clobbered() -> None:
    g = load_graph_from_config("config/relationships.yaml")
    before = g.entity("XAUUSD").entity_type
    add_chain_to_graph(SupplyChain("c", ("GOLD", "XAUUSD"), terminal_instrument="XAUUSD"), g)
    assert g.entity("XAUUSD").entity_type is before  # respected


# --- cross-market (§149, TC-ADR-030) ---

def test_propagation_paths_present() -> None:
    assert PROPAGATION_PATHS["OIL"][0] == "OIL"
    assert "EUROPEAN_ENERGY" in PROPAGATION_PATHS


def test_cleanest_expression_prefers_fewer_hops() -> None:
    near = CrossMarketCandidate("DAX", 0.8, hops=1, permission=MarketPermission.SHADOW_TRADABLE)
    far = CrossMarketCandidate("US500", 0.8, hops=4, permission=MarketPermission.SHADOW_TRADABLE)
    assert cleanest_expression([far, near]).instrument == "DAX"


def test_untradable_never_selected() -> None:
    only = CrossMarketCandidate("EURGBP", 0.95, hops=1,
                                permission=MarketPermission.INTELLIGENCE_ONLY)
    assert cleanest_expression([only]) is None   # observation != authority to trade (§133)
    assert rank_expressions([only])[0].cleanliness == 0.0


def test_illiquid_penalised() -> None:
    liquid = CrossMarketCandidate("US500", 0.8, 2, MarketPermission.SHADOW_TRADABLE,
                                  liquidity_score=1.0)
    thin = CrossMarketCandidate("UK100", 0.8, 2, MarketPermission.SHADOW_TRADABLE,
                                liquidity_score=0.3)
    assert cleanest_expression([thin, liquid]).instrument == "US500"


def test_crossmarket_convergence_input() -> None:
    c = CrossMarketCandidate("XAUUSD", 0.7, 2, MarketPermission.SHADOW_TRADABLE)
    di = crossmarket_convergence_input(c, ImpactDirection.BULLISH, driver="BOND_YIELDS")
    assert di.domain is ConvergenceDomain.CROSS_MARKET
    assert di.correlation_group == "crossmarket:BOND_YIELDS"
