# Safelog — Backlog

Epics and stories for the build phases. Every story has concrete, checkable acceptance criteria —
no vibes. The first story of Epic 1 is the wow moment: it must land before anything else.

## Epic 1 — Core streaming redaction engine

- [x] **Wow moment: redact a log full of fake secrets, inline, in real time**
  - `cat fixtures/sample.log | python3 -m safelog` redacts the AWS secret, Stripe key, email, and
    IP while leaving timestamps and log levels untouched, matching the README demo output exactly.
  - An automated test runs the CLI against `fixtures/sample.log` and asserts the exact redacted
    output byte-for-byte, so the demo can't silently regress.

- [x] **True line-buffered streaming (no whole-stream buffering)**
  - Piping a continuously-appended stream (e.g. `yes "line" | safelog`) produces redacted output
    continuously, not only after EOF.
  - Memory usage stays flat, not proportional to input size, when piping a multi-GB log file.

- [x] **Graceful handling of partial and very long lines**
  - A single line longer than 1MB with no newline is processed in bounded chunks without hanging
    or crashing.
  - A stream that ends without a trailing newline still flushes and redacts its final partial line.

## Epic 2 — Detector coverage & configurability

- [x] **GitLab token detector**
  - A GitLab personal access token (`glpat-` prefix) is redacted as `[REDACTED:gitlab-token]`.
  - Existing GitHub and Slack detector tests still pass unmodified (no regression).

- [x] **PEM private key block detection (multi-line)**
  - A `-----BEGIN ... PRIVATE KEY----- ... -----END ... PRIVATE KEY-----` block spanning multiple
    lines is fully redacted as a single `[REDACTED:private-key]` span, not leaked line-by-line.
  - Detection works when the block arrives split across an arbitrary number of stdin reads (a
    streaming state machine, not a single-line regex).

- [x] **IPv6 address detection**
  - A valid IPv6 address (e.g. `2001:db8::1`) is redacted as `[REDACTED:ip]`.
  - Common non-secret shapes that superficially resemble IPv6 (e.g. `::`) don't trigger false
    positives that mangle normal log lines.

- [x] **Per-detector enable/disable via CLI flags**
  - `safelog --disable email` leaves email addresses untouched while still redacting other types.
  - `safelog --list-detectors` prints every detector name usable with `--disable`.

- [ ] **Config file support for custom patterns and detector toggles**
  - A config file (e.g. `safelog.toml`) defining a custom named regex causes matching text to be
    redacted under that name.
  - Running with no config file present falls back to built-in defaults with no error.

- [x] **Selectable redaction mode**
  - `--mode hash` replaces each distinct secret with a stable short hash, so repeated occurrences
    of the same secret show the same token across the stream without revealing it.
  - `--mode mask` replaces every secret with a fixed `***`, with no `[REDACTED:...]` label leaking
    which detector fired.

## Epic 3 — Entropy-based fallback detection

- [ ] **Shannon-entropy scorer for token-like substrings**
  - A 32+ char random alphanumeric string with no recognizable vendor prefix is flagged and
    redacted as `[REDACTED:high-entropy]` when no regex detector matches it.
  - Common English words and expected log tokens (UUIDs, file paths) are not flagged at the
    default threshold.

- [ ] **Tunable entropy threshold**
  - `--entropy-threshold <float>` changes sensitivity: a test asserts a borderline string is
    flagged at a low threshold and passed through at a high one.

- [ ] **Entropy detector runs only where regex found nothing**
  - A line containing both a regex-matched secret (e.g. a Stripe key) and adjacent high-entropy
    text doesn't double-flag or corrupt the already-redacted regex match.

## Epic 4 — Packaging, docs & polish

- [ ] **Publish to PyPI as `safelog`**
  - `pip install safelog` installs a working `safelog` console command.
  - The installed package's `--version` output matches `pyproject.toml`'s declared version.

- [ ] **`--version` and `--help` flags**
  - `safelog --version` prints the package version and exits 0.
  - `safelog --help` documents every flag added across this backlog (`--disable`, `--mode`,
    `--entropy-threshold`, `--list-detectors`).

- [ ] **Documented performance benchmark**
  - A benchmark script measures added latency per MB piped through safelog vs. raw `cat`, and the
    measured number is recorded in the README or docs.
  - Latency overhead stays under a stated, checkable budget (e.g. <5ms per 1000 lines) on the
    benchmark's own reference log.
