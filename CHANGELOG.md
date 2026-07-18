# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `.gitleaks.toml`, allowlisting the known-fake secrets in `tests/`, `fixtures/`, and
  `scripts/benchmark.py` that exercise safelog's own detectors, and a CI job that runs gitleaks on
  every push and PR.
- `[project.urls]` in `pyproject.toml` (Homepage, Repository, Issues, Changelog) for the PyPI
  listing.

### Fixed

- `python3 -m safelog` in the README's wow-moment demo and no-install run path raised
  `ModuleNotFoundError` from a bare clone; both now carry the `PYTHONPATH=src` the src-layout
  package needs when it isn't installed. Same fix applied to `docs/ARCHITECTURE.md` and
  `site/index.html`.
- The hero terminal's `[REDACTED:...]` chip used a stray 4px border radius instead of the 6px
  inline-chip token from `docs/DESIGN.md`.

## [1.0.0] - 2026-07-17

### Added

- Initial scaffold: streaming CLI, regex-based detectors for AWS keys, Stripe keys, GitHub/Slack
  tokens, JWTs, emails, and IPv4 addresses.
- CI workflow running ruff and pytest on Python 3.9 and 3.12.
- Bounded, streaming stdin reader (`os.read`-based) so a live pipe stays responsive and an
  unterminated line can't grow memory without limit.
- GitLab token and IPv6 address detectors.
- Multi-line PEM private key block detection, collapsed to a single `[REDACTED:private-key]`
  regardless of how many stdin reads the block arrives split across.
- Selectable redaction modes: `--mode label` (default), `--mode mask`, `--mode hash`.
- `--disable`/`--list-detectors` flags for per-detector toggling.
- `--config` flag and `safelog.toml` support for custom regex patterns and a disabled-detector
  list, via a minimal stdlib-only TOML subset parser.
- `docs/ARCHITECTURE.md` describing the codebase's module layout and data flow.
- Shannon-entropy fallback detector (`[REDACTED:high-entropy]`) for secrets with no known vendor
  shape, running only on spans the regex detectors left untouched. Tunable via
  `--entropy-threshold`; toggleable via `--disable high-entropy`.
- `--version` flag.
- `scripts/benchmark.py`, measuring safelog's added latency vs. a raw pass-through baseline and
  recording it against a stated, checkable budget.
- Marketing landing page (`site/index.html`) and its design direction (`docs/DESIGN.md`).
- dev.to launch article (`docs/launch/devto.md`).

### Fixed

- An early downstream pipe close (`safelog | head`, quitting a pager, an agent that stopped
  reading) raised an unhandled `BrokenPipeError` and dumped a traceback with exit 120; safelog now
  redirects stdout to `/dev/null` and exits 141, like any signalled pipe member.

- A private key with `BEGIN`/`END` markers on a single line bypassed the PEM state machine
  entirely and leaked verbatim instead of collapsing to `[REDACTED:private-key]`.
- A `safelog.toml` custom pattern that failed to compile as a regex crashed the CLI instead of
  being skipped like other malformed config lines.
- `--config` pointing at a directory (or any non-missing-file I/O error) crashed the CLI instead
  of falling back to defaults.
- The email detector's unbounded quantifiers caused quadratic-time backtracking on a long line
  with no `@`, stalling the process on an oversized token or blob; both parts are now bounded to
  their real-world maximums.
