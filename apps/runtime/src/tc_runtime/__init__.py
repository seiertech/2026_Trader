"""tc_runtime — orchestration that walks the golden path end to end (§123).

Phase-0/1 runtime: drives the replay clock and threads market data through the
deterministic engines (quant → regime → strategy → risk-sized shadow trade →
outcome → metrics). It is intentionally thin — the engines hold the logic; the
runtime only sequences them and enforces the operating mode.

This is NOT a strategy research harness with an edge claim. It proves the pipeline
is wired correctly on XAUUSD (§123) before any breadth (§161).
"""

from tc_runtime.golden_path import GoldenPathResult, run_golden_path

__all__ = ["GoldenPathResult", "run_golden_path"]
