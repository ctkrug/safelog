# Safelog — Vision

## The problem

The new default workflow for debugging is "pipe my terminal/logs to an AI agent and ask what's
wrong." That's genuinely useful — and it means whatever secrets happen to be sitting in that
output get handed to a third party without a second thought. A stack trace that dumps an `.env`.
A CI log with an embedded Stripe key. A crash report with an internal IP or a customer's email.

Existing secret scanners (gitleaks, truffleHog, detect-secrets) assume a **file at rest** and a
**batch job**: scan the repo, scan the commit, produce a report. None of them are built to sit
**inline in a live pipe**, redacting as bytes fly through, fast enough that a human or an agent on
the other end never notices the delay. That's a different problem: streaming, not batch;
low-latency, not thorough-but-slow; safe-by-default, not opt-in.

## Who it's for

Anyone who pipes logs, command output, or a terminal session into something that shouldn't see
raw secrets — most immediately, developers feeding `tail -f` / CI logs / crash dumps into an AI
coding agent. Also useful for screen-sharing a terminal, piping logs to a third-party support
tool, or sanitizing output before it's pasted into a ticket or Slack.

## The core idea

A single Python file, zero third-party dependencies, that reads stdin and writes stdout one line
at a time. Each line is run through a chain of detectors; anything they flag is replaced with a
labeled placeholder (`[REDACTED:<kind>]`) so the *shape* of the log is preserved — you can still
tell an AWS key was there and roughly where — without leaking the value itself.

Two layers of detection, doing different jobs:

1. **Regex detectors** for known secret shapes — AWS keys, Stripe/GitHub/Slack tokens, JWTs,
   private key blocks, emails, IPs. Precise, fast, zero false-negatives for the formats they know.
2. **Entropy-based fallback** for the long tail regex can't name — generic API keys, passwords,
   hashes — flagged by Shannon entropy over a sliding window of token-like substrings. Higher
   recall, tunable false-positive rate.

Zero dependencies is a deliberate constraint, not an accident: a tool that sits inline in your
pipe and touches every byte of your logs needs to be small enough to read start to finish and
trust, and simple enough to vendor as one file into an environment where installing a package
isn't an option.

## Key design decisions

- **Line-oriented streaming, not whole-stream buffering.** Safelog must not materially add latency
  to a live pipe. Reading and redacting one line at a time (falling back to bounded chunk reads
  for pathologically long lines) keeps memory flat and output responsive regardless of stream
  length.
- **Redact the secret, not the line.** Replacing an entire matched line with a placeholder would
  destroy debugging context (timestamps, log level, which service). Detectors capture just the
  sensitive span and replace only that, so everything else — including *that a secret was there*
  — stays visible.
- **Labeled placeholders over a single generic mask.** `[REDACTED:stripe-key]` instead of
  `***` tells the reader (human or agent) what kind of thing was removed, which matters for
  triage, without revealing enough to be useful to an attacker.
- **Stdlib only, one file.** No supply-chain surface, no version drift, no install friction —
  `curl` it, `pip install` it, or paste it into a script. A tool whose entire job is handling
  secrets should be trivially auditable.
- **Regex first, entropy as fallback, not the other way around.** Regex detectors are precise and
  cheap to run on every line; entropy scanning is comparatively expensive and prone to false
  positives, so it only runs where regex didn't already find something to flag.
- **Configurable, but safe by default.** Ships with sane defaults for every known detector so
  `cmd | safelog` is useful with zero configuration; power users can disable detectors, add custom
  patterns, or tune the entropy threshold via flags or a config file.

## What "v1 done" looks like

- All the detectors in the README's planned-features list are implemented and covered by tests:
  AWS keys, GitHub/GitLab/Slack tokens, Stripe keys, JWTs, PEM private key blocks, emails, IPv4/IPv6.
- The entropy-based fallback detector is implemented, tunable, and demonstrably catches at least
  one class of secret none of the regex detectors would (e.g., a generic 32-char API key with no
  recognizable prefix).
- `cat fixtures/sample.log | safelog` reproduces the README's wow-moment demo exactly, and that
  demo is exercised by an automated test so it can't silently regress.
- The CLI supports redaction-mode selection (labeled placeholder vs. fixed mask vs. stable hash)
  and per-detector enable/disable via flags.
- Streaming behavior is verified under load: piping a large, continuously-appended log
  (`tail -f`-style) produces redacted output with no perceptible added latency and flat memory use.
- README, VISION, and BACKLOG all stay in sync with the actual feature set — no planned feature
  described as if it were shipped.
