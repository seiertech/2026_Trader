"""Health-state registry (§103) with fail-closed aggregation (§104).

Components report their state; the registry aggregates to a system state using the
WORST state observed. Critical-dependency failure yields a state that prevents new
live trades — the caller (risk/decision layer) treats TRADING_DISABLED and CRITICAL
as trade-blocking. Absence of a required component is treated as CRITICAL, not
HEALTHY: we never fail open.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from tc_domain.enums import HealthState
from tc_domain.time import utc_now

# Ordered from best to worst. Aggregation takes the worst.
_SEVERITY: dict[HealthState, int] = {
    HealthState.HEALTHY: 0,
    HealthState.DEGRADED: 1,
    HealthState.TRADING_DISABLED: 2,
    HealthState.CRITICAL: 3,
}

# States in which NEW live trading must not proceed (§104).
_TRADE_BLOCKING: frozenset[HealthState] = frozenset(
    {HealthState.TRADING_DISABLED, HealthState.CRITICAL}
)


class HealthReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    component: str
    state: HealthState
    detail: str = ""
    at: datetime


class HealthRegistry:
    """Mutable registry of latest component health. Aggregation is fail-closed."""

    def __init__(self, required_components: tuple[str, ...] = ()) -> None:
        self._reports: dict[str, HealthReport] = {}
        self._required = set(required_components)

    def report(self, component: str, state: HealthState, detail: str = "") -> None:
        self._reports[component] = HealthReport(
            component=component, state=state, detail=detail, at=utc_now()
        )

    def require(self, component: str) -> None:
        self._required.add(component)

    def system_state(self) -> HealthState:
        """Worst observed state. A required-but-missing component is CRITICAL."""
        if self._required - set(self._reports):
            return HealthState.CRITICAL  # a required component never reported
        if not self._reports:
            return HealthState.CRITICAL  # nothing reported: fail closed
        return max(
            (r.state for r in self._reports.values()),
            key=lambda s: _SEVERITY[s],
        )

    def trading_allowed(self) -> bool:
        """True only if the aggregate state permits new trades (§104)."""
        return self.system_state() not in _TRADE_BLOCKING

    def snapshot(self) -> tuple[HealthReport, ...]:
        return tuple(self._reports.values())
