# Safelog

**▶ Live site · [apps.charliekrug.com/safelog](https://apps.charliekrug.com/safelog/)**

[![CI](https://github.com/ctkrug/safelog/actions/workflows/ci.yml/badge.svg)](https://github.com/ctkrug/safelog/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

**Keep secrets out of your AI agent's logs.**

A zero-dependency streaming filter you pipe logs or terminal output through before an AI agent
(or a human, or a screen-share) sees them. It redacts API keys, tokens, emails, and IP addresses
inline, in real time, without buffering the whole stream.

```
tail -f app.log | safelog | claude
some-flaky-cli --verbose 2>&1 | safelog
cat crash-dump.txt | safelog
```

## Why

The moment you start piping your terminal or logs into an AI agent ("here's the output, tell me
what's wrong"), you've handed it whatever secrets happened to be sitting in that stream. Cloud API
keys in a stack trace, a `.env` dump from a debug print, an internal IP an agent doesn't need. Most
redaction tools assume a file on disk and a batch job. Safelog assumes a live pipe: stdin in,
stdout out, one line at a time, low enough latency that it's invisible in an interactive session.

It's under 500 lines of stdlib-only Python across eight small modules. Read it, vendor it, trust it.

## See it work

Pipe a log file full of fake API keys and stack traces through `safelog` and watch every secret
get redacted inline, in real time, while everything else (timestamps, stack frames, log
levels) passes through untouched.

```
$ cat fixtures/sample.log | PYTHONPATH=src python3 -m safelog
2026-07-17T12:00:01Z INFO  starting worker pool=4
2026-07-17T12:00:02Z ERROR AWS_SECRET_ACCESS_KEY=[REDACTED:aws-secret]
2026-07-17T12:00:03Z ERROR stripe key sk_test_[REDACTED:stripe-key] rejected
2026-07-17T12:00:04Z WARN  contact [REDACTED:email] about quota
2026-07-17T12:00:05Z INFO  client [REDACTED:ip] connected
```

## Features

- **Streaming, not batch.** Reads stdin line-by-line, falling back to bounded chunks for lines
  without a trailing newline, and writes as it goes, safe to sit inline in a live `|` pipe with
  flat memory use regardless of stream length.
- **Regex detectors** for well-known secret shapes: AWS keys, GitHub/GitLab tokens, Stripe keys,
  Slack tokens, private key blocks (`-----BEGIN ... PRIVATE KEY-----`, collapsed across however
  many lines they span), JWTs, emails, IPv4/IPv6.
- **Configurable redaction modes**: `--mode label` (default, `[REDACTED:aws-secret]`),
  `--mode mask` (`***`, no detector name leaked), or `--mode hash` (a stable per-secret hash, so
  repeated occurrences of the same secret show the same token without revealing it).
- **Per-detector toggles**: `safelog --disable email` leaves email addresses untouched;
  `safelog --list-detectors` prints every name usable with `--disable`.
- **Config file support**: a `safelog.toml` (or `--config PATH`) can add custom named patterns
  and a list of disabled detectors; no config file present just falls back to the defaults.
- **Entropy-based fallback detector** catches the long tail regex can't name (generic API keys,
  passwords, and other high-entropy tokens with no recognizable vendor prefix) by scoring
  Shannon entropy over token-like substrings. Runs only where a regex detector found nothing, so
  it never re-flags or corrupts an already-redacted secret. Tune sensitivity with
  `--entropy-threshold`, or disable it entirely with `--disable high-entropy`.
- **Zero dependencies.** Stdlib only. Works anywhere Python 3.9+ runs.

## Install

Safelog needs only Python 3.9+ and the standard library.

```
pip install "git+https://github.com/ctkrug/safelog"   # installs the `safelog` command
```

Or run it straight from a clone, no install needed:

```
git clone https://github.com/ctkrug/safelog
cd safelog
PYTHONPATH=src python3 -m safelog < app.log
```

Because it is one stdlib-only package, you can also vendor `src/safelog/` into a project and call
`PYTHONPATH=src python3 -m safelog` with nothing to install.

## Usage

```
safelog --mode mask                       # replace every secret with ***
safelog --mode hash                       # stable per-secret hash instead of a label
safelog --disable email --disable ip      # leave those two detector types untouched
safelog --list-detectors                  # print every detector name
safelog --config ./safelog.toml           # load custom patterns / disabled list from a file
safelog --entropy-threshold 3.5           # lower the bar for flagging high-entropy tokens
```

A config file looks like:

```toml
[patterns]
internal-id = "INTERNAL-[0-9]{6}"

[detectors]
disabled = ["email", "ip"]
```

## Performance

Safelog is line-oriented and adds only the cost of running its detectors over each line.
`scripts/benchmark.py` measures that overhead against a raw pass-through baseline on a mixed
secret/plain-line reference log:

```
PYTHONPATH=src python3 scripts/benchmark.py
```

On the reference log it typically measures **60 to 125ms of added latency per 1000 lines**
(well under the script's own 200ms/1000-line budget, which it fails the run if exceeded).

## Roadmap

- **Publish to PyPI** so `pip install safelog` works without the `git+` URL.

## Stack

Python 3, standard library only. No third-party runtime dependencies; dev-only tooling
(`pytest`, `ruff`) lives in the `dev` extra.

## Status

Core streaming redaction engine and detector coverage/configurability are implemented and
tested. See [`docs/VISION.md`](docs/VISION.md) for the design,
[`docs/BACKLOG.md`](docs/BACKLOG.md) for the build plan, and
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the code is organized.

## License

MIT. See [`LICENSE`](LICENSE).

---

More of Charlie's projects → [apps.charliekrug.com](https://apps.charliekrug.com)
