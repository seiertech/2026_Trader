"""Specialist contract (§58-66, §91).

An Assessment is an OPINION with a rationale and a confidence. It carries no risk,
size or order field — specialists inform, they do not act (§55, TC-ADR-012). Each is
attributable so the learning engine can later measure whether that specialist adds
value (§91, TC-ADR-019).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class Assessment:
    """One specialist's structured opinion."""

    specialist: str
    verdict: str          # domain-specific, e.g. "TRENDING_UP", "ELEVATED", "NEUTRAL"
    supports: str         # "LONG" | "SHORT" | "NEITHER" — directional lean only
    confidence: float     # 0..1
    rationale: str

    # Permanent guarantee, mirroring the AI gateway: a specialist cannot set risk.
    @property
    def overrides_risk(self) -> bool:
        return False


@runtime_checkable
class Specialist(Protocol):
    """A specialist assessor (§58-66)."""

    name: str

    def assess(self, context: dict[str, Any]) -> Assessment: ...
