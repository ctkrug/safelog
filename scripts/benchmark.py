#!/usr/bin/env python3
"""Measure safelog's redaction overhead vs. a raw pass-through baseline.

Run directly to print a report:

    PYTHONPATH=src python3 scripts/benchmark.py
"""

import time

from safelog.redact import Redactor

BUDGET_MS_PER_1000_LINES = 200.0

REFERENCE_LINES = [
    "2026-07-17T12:00:00Z INFO  starting worker pool=4\n",
    "2026-07-17T12:00:01Z ERROR AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY\n",
    "2026-07-17T12:00:02Z ERROR stripe key sk_test_NOTREALZZZ rejected\n",
    "2026-07-17T12:00:03Z WARN  contact jane.doe@example.com about quota\n",
    "2026-07-17T12:00:04Z INFO  client 10.0.4.212 connected\n",
    "2026-07-17T12:00:05Z INFO  request completed in 42ms status=200\n",
    "2026-07-17T12:00:06Z DEBUG cache hit for key=user:1234:profile\n",
]


def build_reference_log(n_lines: int) -> list:
    """Cycle REFERENCE_LINES up to ``n_lines`` entries — a realistic secret/plain-line mix."""
    return [REFERENCE_LINES[i % len(REFERENCE_LINES)] for i in range(n_lines)]


def measure_overhead_ms_per_1000_lines(lines: list) -> float:
    """Return safelog's added latency vs. a no-op pass-through, in ms per 1000 lines."""
    start = time.perf_counter()
    for line in lines:
        _ = line
    baseline_seconds = time.perf_counter() - start

    redactor = Redactor()
    start = time.perf_counter()
    for line in lines:
        redactor.process_line(line)
    redact_seconds = time.perf_counter() - start

    overhead_seconds = redact_seconds - baseline_seconds
    return (overhead_seconds / len(lines)) * 1000 * 1000


def main() -> int:
    lines = build_reference_log(20_000)
    overhead = measure_overhead_ms_per_1000_lines(lines)
    print(f"safelog overhead: {overhead:.3f} ms per 1000 lines ({len(lines)} lines measured)")
    print(f"budget: {BUDGET_MS_PER_1000_LINES:.1f} ms per 1000 lines")
    if overhead > BUDGET_MS_PER_1000_LINES:
        print("FAIL: overhead exceeds budget")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
