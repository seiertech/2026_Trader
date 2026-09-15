"""tc_macro — Macro & monetary-policy intelligence (§46, §63, §150).

Models an economic release the way the spec requires (§46): event, forecast, actual,
previous, surprise, timestamp. The SURPRISE (actual vs forecast, normalised) is what
carries market information — not the headline number.

Produces a MACRO_MONETARY convergence input (§150) whose direction depends on the
release's polarity: for some series a positive surprise is bullish for the currency
(e.g. CPI → hawkish → currency up), for others it is bearish (e.g. unemployment up →
growth concern). That mapping is explicit and configurable, never guessed.
"""

from tc_macro.releases import (
    MacroRelease,
    SurpriseDirection,
    macro_convergence_input,
    surprise_score,
)

__all__ = [
    "MacroRelease",
    "SurpriseDirection",
    "surprise_score",
    "macro_convergence_input",
]
