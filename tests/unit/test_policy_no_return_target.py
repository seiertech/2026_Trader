"""V1 has no capital return target (§0 Prime Directive, §75, TC-ADR-017)."""

from __future__ import annotations

import pytest
from tc_domain.policy import (
    RETURN_TARGET_FORBIDDEN,
    PolicyViolation,
    assert_no_return_target,
)


@pytest.mark.parametrize("empty", [None, "", 0, 0.0, False])
def test_absent_target_is_allowed(empty: object) -> None:
    assert_no_return_target(empty)  # does not raise


@pytest.mark.parametrize("target", [25000, 25_000.0, "25000", "£25,000", 1, True])
def test_any_return_target_is_a_violation(target: object) -> None:
    with pytest.raises(PolicyViolation) as exc:
        assert_no_return_target(target)
    assert exc.value.code == RETURN_TARGET_FORBIDDEN
