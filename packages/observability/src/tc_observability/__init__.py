"""tc_observability — structured logging, health and audit (Part XXIII).

  * structured JSON logging with UTC timestamps (§125);
  * health-state model (§103) that fails closed (§104);
  * an append-only audit trail — every important action is timestamped and
    recorded (§105), and audit records are never mutated or deleted.
"""

from tc_observability.audit import AuditEvent, AuditLog
from tc_observability.health import HealthRegistry, HealthReport
from tc_observability.logging import configure_logging, get_logger

__all__ = [
    "AuditEvent",
    "AuditLog",
    "HealthReport",
    "HealthRegistry",
    "configure_logging",
    "get_logger",
]
