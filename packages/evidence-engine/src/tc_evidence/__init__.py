"""tc_evidence — the Evidence Pack builder (Part X, §43, §44, §89, §90).

Before a trading decision is made, an immutable Evidence Pack SHALL be created (§43).
It is the frozen snapshot of everything known at the decision timestamp — the thing
the AI reasons over (§44) and the audit/attribution layers reference forever. It never
changes (§90, TC-ADR-018); a reassessment is a separate pack.

This builder assembles a pack from what the pipeline knows at decision time (regime,
convergence result, strategy setup, sizing audit). As the intelligence engines land
(macro, news, cross-market, historical), they contribute additional domain evidence
and context to the same pack — no parallel structure.
"""

from tc_evidence.builder import build_evidence_pack, pack_id_for

__all__ = ["build_evidence_pack", "pack_id_for"]
