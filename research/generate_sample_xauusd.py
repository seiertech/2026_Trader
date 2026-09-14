"""Generate a deterministic synthetic XAUUSD 1-minute dataset for Shadow replay.

This is SAMPLE data for building/testing the golden path offline — NOT real market
data and NOT to be mistaken for it. It is flagged as synthetic in provenance. Real
history arrives via the MT5 provider on the Windows edge (Phase 1/2, ADR-032).

Deterministic (fixed seed) so tests are reproducible. Produces a gently trending,
mean-reverting gold-like series with an intraday session shape. One trading week of
1-minute bars.

Usage:  python research/generate_sample_xauusd.py
Writes: data/reference/XAUUSD_1m_sample.csv
"""

from __future__ import annotations

import csv
import math
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

SEED = 20260914
START = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)  # a Monday, midnight UTC
DAYS = 5
MINUTES_PER_DAY = 24 * 60
START_PRICE = 2650.00
OUT = Path(__file__).resolve().parents[1] / "data" / "reference" / "XAUUSD_1m_sample.csv"


def main() -> None:
    rng = random.Random(SEED)
    price = START_PRICE
    # A slow drift + mean reversion toward a wandering anchor gives realistic structure.
    anchor = START_PRICE
    rows: list[dict[str, str]] = []

    total = DAYS * MINUTES_PER_DAY
    for i in range(total):
        t = START + timedelta(minutes=i)
        minute_of_day = i % MINUTES_PER_DAY

        # Volatility rises around the London/NY overlap (~13:00-17:00 UTC).
        session = 0.6 + 0.9 * math.exp(-((minute_of_day - 15 * 60) ** 2) / (2 * (150**2)))
        vol = 0.18 * session  # per-minute stdev in price units

        # Anchor wanders slowly (regime drift).
        anchor += rng.gauss(0, 0.05)
        # Mean-reverting step toward the anchor plus noise.
        drift = 0.002 * (anchor - price)
        step = drift + rng.gauss(0, vol)

        o = price
        c = price + step
        hi = max(o, c) + abs(rng.gauss(0, vol * 0.5))
        lo = min(o, c) - abs(rng.gauss(0, vol * 0.5))
        v = max(1, int(abs(rng.gauss(0, 1)) * 400 * session))
        price = c

        rows.append(
            {
                "open_time": t.isoformat(),
                "open": f"{o:.2f}",
                "high": f"{hi:.2f}",
                "low": f"{lo:.2f}",
                "close": f"{c:.2f}",
                "volume": str(v),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["open_time", "open", "high", "low", "close", "volume"])
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {len(rows)} bars to {OUT}")
    print(f"first: {rows[0]['open_time']}  last: {rows[-1]['open_time']}")
    print(f"start {rows[0]['open']}  end {rows[-1]['close']}")


if __name__ == "__main__":
    main()
