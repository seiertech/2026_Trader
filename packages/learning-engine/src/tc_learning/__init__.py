"""tc_learning — the Learning Engine (Part XX, §49–§53, §88–§93).

Turns accumulated experience into knowledge about where edge actually exists — the
Prime Directive's whole purpose (§0, §130). Phase-11 slice:

  * forward-outcome labelling (§49): what the market did over 5m/15m/30m/1h/4h/1d
    after every opportunity — traded AND rejected (§50);
  * per-cell attribution (§91): group outcomes by instrument/regime/strategy/direction
    and report expectancy, win rate, sample size, profit factor;
  * small-sample honesty (§53): cells below a minimum sample are flagged WEAK — the
    system never treats "8/10 wins" as strong evidence.

All statistics are deterministic. No AI, no edge presumed (TC-ADR-020).
"""

from tc_learning.attribution import (
    CellStats,
    EvidenceStrength,
    attribute,
)
from tc_learning.labelling import (
    ForwardLabel,
    label_forward_outcomes,
)

__all__ = [
    "ForwardLabel",
    "label_forward_outcomes",
    "CellStats",
    "EvidenceStrength",
    "attribute",
]
