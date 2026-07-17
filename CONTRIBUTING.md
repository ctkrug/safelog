# Contributing

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Workflow

```
pytest -q          # run the test suite
ruff check .        # lint
```

Both must pass before opening a PR — CI runs the same two commands on Python 3.9 and 3.12.

## Adding a detector

Detectors live in `src/safelog/detectors.py` as a `Detector(name, pattern)` pair, where `pattern`
is a compiled regex with a `secret` named group marking the span to redact. Add the detector to
`DETECTORS`, then add a test in `tests/test_redact.py` asserting the secret is replaced and the
raw value no longer appears in the output.

When adding an example secret to a fixture, test, or the README, keep it obviously fake (e.g. an
all-caps placeholder rather than a realistic random string) — GitHub's push protection will block
values that are structurally close enough to a real credential, even clearly-labeled test data.
