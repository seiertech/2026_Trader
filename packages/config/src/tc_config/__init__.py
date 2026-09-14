"""tc_config — typed configuration loader for Trading Command.

Loads the YAML files under ``config/`` into validated, typed objects. Configuration
is the seam through which the deterministic policy tier is applied at startup:

  * the loaded instrument universe is checked for crypto (TC-ADR-006);
  * ``runtime.return_target`` is asserted absent (Prime Directive §0, TC-ADR-017);
  * ``mode`` defaults to and is validated against the operating-mode enum, SHADOW
    being the mandatory initial mode (§79).

Validation failures raise loudly. Fail closed (§104, Part XXXI §7).
"""

from tc_config.loader import (
    ConfigError,
    RiskConfig,
    RuntimeConfig,
    TradingCommandConfig,
    load_config,
)

__all__ = [
    "ConfigError",
    "RiskConfig",
    "RuntimeConfig",
    "TradingCommandConfig",
    "load_config",
]
