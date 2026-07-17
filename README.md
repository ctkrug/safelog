# Safelog

[![CI](https://github.com/ctkrug/safelog/actions/workflows/ci.yml/badge.svg)](https://github.com/ctkrug/safelog/actions/workflows/ci.yml)

A zero-dependency streaming filter you pipe logs or terminal output through before an AI agent
(or a human, or a screen-share) sees them. It redacts API keys, tokens, emails, and IP addresses
inline, in real time, without buffering the whole stream.

```
tail -f app.log | safelog | claude
some-flaky-cli --verbose 2>&1 | safelog
cat crash-dump.txt | safelog
```

## Why

The moment you start piping your terminal or logs into an AI agent — "here's the output, tell me
what's wrong" — you've handed it whatever secrets happened to be sitting in that stream. Cloud API
keys in a stack trace, a `.env` dump from a debug print, an internal IP an agent doesn't need. Most
redaction tools assume a file on disk and a batch job. Safelog assumes a live pipe: stdin in,
stdout out, one line at a time, low enough latency that it's invisible in an interactive session.

It's a single Python file with no third-party dependencies — read it, vendor it, trust it.

## The wow moment

Pipe a log file full of fake API keys and stack traces through `safelog` and watch every secret
get redacted inline, in real time, while everything else — timestamps, stack frames, log
levels — passes through untouched.

```
$ cat fixtures/sample.log | python3 -m safelog
2026-07-17T12:00:01Z INFO  starting worker pool=4
2026-07-17T12:00:02Z ERROR AWS_SECRET_ACCESS_KEY=[REDACTED:aws-secret]
2026-07-17T12:00:03Z ERROR stripe key sk_test_[REDACTED:stripe-key] rejected
2026-07-17T12:00:04Z WARN  contact [REDACTED:email] about quota
2026-07-17T12:00:05Z INFO  client [REDACTED:ip] connected
```

## Planned features

- **Streaming, not batch.** Reads stdin line-by-line (or in bounded chunks for lines without
  trailing newlines), writes as it goes — safe to sit inline in a live `|` pipe.
- **Regex detectors** for well-known secret shapes: AWS keys, GitHub/GitLab tokens, Stripe keys,
  Slack tokens, private key blocks (`-----BEGIN ... PRIVATE KEY-----`), JWTs, emails, IPv4/IPv6.
- **Entropy-based fallback detector** for the long tail: high-entropy tokens (generic API keys,
  passwords, hashes) that don't match a known vendor shape but look like secrets by Shannon
  entropy over a sliding window.
- **Configurable redaction** — replace with a fixed placeholder, a labeled placeholder
  (`[REDACTED:aws-secret]`), or a stable per-secret hash (so repeated occurrences of the same
  secret are visibly the same token without revealing it).
- **Allow/deny tuning** via CLI flags and an optional config file — disable a detector, raise or
  lower the entropy threshold, add custom regex patterns.
- **Zero dependencies.** Stdlib only. One file. Works anywhere Python 3 runs.

## Stack

Python 3, standard library only. No third-party runtime dependencies — dev-only tooling
(`pytest`, `ruff`) lives in the `dev` extra.

## Status

Early scaffold — see [`docs/VISION.md`](docs/VISION.md) for the design and
[`docs/BACKLOG.md`](docs/BACKLOG.md) for the build plan.

## License

MIT — see [`LICENSE`](LICENSE).
