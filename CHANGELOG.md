# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
