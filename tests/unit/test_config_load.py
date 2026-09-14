"""Config loads, validates, and enforces the policy tier at startup (fail closed)."""

from __future__ import annotations

from pathlib import Path

import pytest
from tc_config import ConfigError, load_config
from tc_config.loader import REQUIRED_RISK_CONTROLS
from tc_domain.enums import OperatingMode

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def test_default_config_loads() -> None:
    cfg = load_config(CONFIG_DIR)
    # SHADOW is the mandatory initial mode (§79).
    assert cfg.runtime.mode is OperatingMode.SHADOW
    # No return target (§0, TC-ADR-017).
    assert cfg.runtime.return_target is None
    # Reference unit is £250 (§74, TC-ADR-016).
    assert cfg.runtime.reference_unit_gbp == 250


def test_all_risk_controls_present() -> None:
    cfg = load_config(CONFIG_DIR)
    assert set(cfg.risk.risk_controls) >= REQUIRED_RISK_CONTROLS
    # 17 original §77 controls + KELLY_FRACTION (§77a, TC-CR-001) = 18.
    assert len(REQUIRED_RISK_CONTROLS) == 18
    assert "KELLY_FRACTION" in REQUIRED_RISK_CONTROLS


def test_kelly_fraction_default_is_quarter() -> None:
    cfg = load_config(CONFIG_DIR)
    assert float(cfg.risk.risk_controls["KELLY_FRACTION"]) == 0.25  # §77a default


def test_kelly_fraction_above_cap_fails_closed(tmp_path) -> None:
    # A KELLY_FRACTION over 0.50 (full-Kelly-ward) must be rejected at load (§77a).
    import shutil

    cfgdir = tmp_path / "config"
    shutil.copytree(CONFIG_DIR, cfgdir)
    risk = (cfgdir / "risk.yaml").read_text().replace(
        "KELLY_FRACTION:           0.25", "KELLY_FRACTION:           0.75"
    )
    (cfgdir / "risk.yaml").write_text(risk)
    with pytest.raises(ConfigError):
        load_config(cfgdir)


def test_eight_canonical_instruments_and_none_live() -> None:
    cfg = load_config(CONFIG_DIR)
    assert len(cfg.instruments) == 8  # TC-ADR-007
    ids = {i.canonical_id for i in cfg.instruments}
    assert ids == {"GBPUSD", "EURUSD", "USDJPY", "NAS100", "US500", "UK100",
                   "XAUUSD", "USOIL"}
    # Live requires an explicit approved build unit (Part XXXI).
    assert all(i.permission.value != "LIVE_TRADABLE" for i in cfg.instruments)


def test_missing_config_dir_fails_closed() -> None:
    with pytest.raises(ConfigError):
        load_config("/nonexistent/config/dir")
