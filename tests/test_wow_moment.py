import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample.log"

EXPECTED = (
    "2026-07-17T12:00:01Z INFO  starting worker pool=4\n"
    "2026-07-17T12:00:02Z ERROR AWS_SECRET_ACCESS_KEY=[REDACTED:aws-secret]\n"
    "2026-07-17T12:00:03Z ERROR stripe key sk_test_[REDACTED:stripe-key] rejected\n"
    "2026-07-17T12:00:04Z WARN  contact [REDACTED:email] about quota\n"
    "2026-07-17T12:00:05Z INFO  client [REDACTED:ip] connected\n"
)


def test_wow_moment_matches_readme_demo_byte_for_byte():
    result = subprocess.run(
        [sys.executable, "-m", "safelog"],
        stdin=FIXTURE.open("rb"),
        capture_output=True,
        check=True,
    )
    assert result.stdout.decode() == EXPECTED
