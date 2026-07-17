import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from benchmark import (  # noqa: E402
    BUDGET_MS_PER_1000_LINES,
    build_reference_log,
    measure_overhead_ms_per_1000_lines,
)

# Generous multiplier over the documented budget: this guards against an
# order-of-magnitude regression, not micro-noise from a shared CI runner.
TEST_BUDGET_MS_PER_1000_LINES = BUDGET_MS_PER_1000_LINES * 3


def test_build_reference_log_cycles_to_requested_length():
    assert len(build_reference_log(0)) == 0
    assert len(build_reference_log(3)) == 3
    assert len(build_reference_log(50)) == 50


def test_overhead_stays_within_budget_on_reference_log():
    lines = build_reference_log(2000)
    overhead = measure_overhead_ms_per_1000_lines(lines)
    assert overhead < TEST_BUDGET_MS_PER_1000_LINES
