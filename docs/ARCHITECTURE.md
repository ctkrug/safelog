# Safelog — Architecture

A map of the codebase for anyone (human or agent) picking this up cold.

## Modules

```
src/safelog/
  __main__.py    # `python3 -m safelog` entrypoint, calls cli.main()
  cli.py         # argparse CLI: --mode, --disable, --list-detectors, --config, --entropy-threshold
  stream.py      # bounded, streaming line reader (iter_stream_lines)
  detectors.py   # regex Detector definitions (AWS, Stripe, GitHub/GitLab, Slack, JWT, email, IP)
  redact.py      # redact_line()/redact_entropy() + stateful Redactor (PEM handling, modes)
  entropy.py     # Shannon-entropy scorer + high-entropy token finder (regex fallback)
  config.py      # minimal stdlib-only TOML-subset parser for safelog.toml
```

## Data flow

```
stdin fd -> iter_stream_lines() -> Redactor.process_line() -> stdout
                                         |
                                         v
                              redact_line() over DETECTORS
                              (+ custom detectors from config)
                                         |
                                         v
                         redact_entropy() over what regex left behind
```

1. `cli.main()` builds an argparse parser, loads `--config` (or the default
   `safelog.toml`, silently absent if there is none), and merges its
   `disabled_detectors`/`custom_detectors` with `--disable`.
2. `stream.iter_stream_lines(fd)` reads raw bytes with `os.read()` — chosen
   over `TextIOWrapper.read()`/iteration because `os.read()` returns as soon
   as *any* data is available, which is what keeps a live `tail -f | safelog`
   pipe responsive. It yields one newline-terminated line at a time, or a
   bounded `max_line_bytes`-sized chunk when a line has no newline yet (so a
   pathologically long or never-terminated line can't grow memory
   unboundedly). It flushes a final partial line at EOF.
3. Each line goes through `redact.Redactor.process_line()`. Redactor is
   stateful only for one thing: a `-----BEGIN ... PRIVATE KEY-----` block,
   which spans multiple lines and must collapse into a single
   `[REDACTED:private-key]` line rather than leaking key material line by
   line. Outside a PEM block, it delegates to the stateless `redact_line()`.
4. `redact_line()` runs every enabled `Detector` (a `(name, compiled regex)`
   pair with a `secret` capture group) over the line in sequence, replacing
   only the captured span so surrounding context (an env var name, a key
   prefix, a timestamp) stays visible.
5. `redact.format_replacement()` renders the placeholder according to
   `--mode`: `label` (`[REDACTED:<name>]`, default), `mask` (`***`, no
   detector name leaked), or `hash` (a stable 8-char hash of the secret
   value, so repeated occurrences of the same secret show the same token).
6. `redact_entropy()` then scans whatever `redact_line()` left behind for
   long token-like runs (`entropy.find_high_entropy_tokens()`) and flags any
   whose Shannon entropy clears `--entropy-threshold`, as
   `[REDACTED:high-entropy]`. Because it runs *after* regex substitution, an
   already-redacted span is just a short placeholder — never long enough to
   be re-flagged. Toggle it off with `--disable high-entropy`.
7. At EOF, `cli.main()` calls `Redactor.flush()` so a stream that ends
   mid-PEM-block still redacts what it buffered instead of dropping it.

## Config file

`config.load_config(path)` parses a small subset of TOML by hand — a
`[patterns]` table of `name = "regex"` custom detectors and a `[detectors]`
table with a `disabled = [...]` list — rather than depending on `tomllib`
(stdlib only from Python 3.11) or a third-party TOML library, to keep the
zero-dependency guarantee across the project's full Python 3.9+ range. A
missing file is not an error; it returns `EMPTY_CONFIG`.

## How to run it

```
cat fixtures/sample.log | PYTHONPATH=src python3 -m safelog   # the wow-moment demo
PYTHONPATH=src python3 -m pytest -q                   # run tests locally (no install needed)
ruff check .                                          # lint
PYTHONPATH=src python3 scripts/benchmark.py           # latency-overhead benchmark
```

CI (`.github/workflows/ci.yml`) installs the package with `pip install -e ".[dev]"`
and runs both `ruff check .` and `pytest -q` on Python 3.9 and 3.12, plus a separate
`secrets` job that runs gitleaks over the full commit history on every push and PR.

## Secrets scanning

`.gitleaks.toml` extends gitleaks' default ruleset with a path allowlist for `tests/`,
`fixtures/`, and `scripts/benchmark.py` — the only places this repo intentionally contains
secret-shaped strings, since they exist to exercise safelog's own detectors. Anywhere else,
a gitleaks hit is real. `tests/test_gitleaks_config.py` guards the allowlist itself against
silent drift.

## Benchmark

`scripts/benchmark.py` measures safelog's added latency over a raw pass-through baseline on a
mixed secret/plain-line reference log, in ms per 1000 lines, and exits non-zero if it clears
`BUDGET_MS_PER_1000_LINES`. `tests/test_benchmark.py` runs the same logic on a smaller log with a
more generous multiplier, as a lightweight CI regression guard rather than a strict perf gate.
