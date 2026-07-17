---
title: "Safelog: redacting secrets from a live log stream before an AI reads them"
published: false
tags: python, cli, security, ai
---

My debugging loop changed this year. When something breaks, I do not read the stack trace first.
I pipe it into an AI agent and ask what happened. It is fast and it usually works.

Then one day I actually looked at what I had pasted in, and it had a live cloud key in it. A debug
print had dumped part of the environment into the log, the log went into the crash report, and the
crash report went straight to a model running on someone else's machine. The secret was already
gone before I noticed it was there.

Existing scanners did not fit. Tools like gitleaks and truffleHog are built to scan a repo or a
commit at rest and produce a report. That is a batch job. I needed the opposite: something that
sits inline in a live pipe and scrubs secrets as bytes flow through, fast enough that I never feel
it. So I wrote Safelog, a zero-dependency CLI you drop into any pipe:

```
tail -f app.log | safelog | claude
```

Here are the two build decisions that turned out to be more interesting than I expected.

## 1. `os.read`, not buffered iteration

The obvious way to read stdin line by line in Python is `for line in sys.stdin`. It is also the
wrong way for this job. Python's buffered text layer waits to fill an internal buffer before it
hands you anything, which means a `tail -f` stream can sit silent for a while and then dump a
batch. For an interactive filter that is the difference between "invisible" and "why did my
terminal freeze."

Safelog reads raw bytes with `os.read` instead, which returns as soon as any data is available,
and does its own newline splitting with an incremental UTF-8 decoder. A line is emitted the moment
its trailing newline arrives.

The catch with owning the buffer is that you also own the failure modes. A stream with no newlines
at all, or one pathologically long line, would grow that buffer without limit. So the reader caps a
pending line at `max_line_bytes` and yields it in bounded chunks, which keeps memory flat no matter
what you throw at it. Piping five megabytes with no newline through it now costs the same memory as
piping five kilobytes.

## 2. Regex first, entropy second

Two layers of detection do different jobs. Regex detectors catch known shapes: AWS keys, Stripe
keys, GitHub and GitLab and Slack tokens, JWTs, PEM private key blocks, emails, IPs. They are
precise and cheap. But they cannot catch a generic 32-character API key with no recognizable
prefix, and there are a lot of those.

For the long tail, a Shannon-entropy pass flags token-like runs that score above a threshold. The
important detail is ordering: entropy runs only over what the regex layer left behind. By the time
it sees a line, any real secret the regex caught is already a short `[REDACTED:...]` placeholder,
too short to look like a secret, so the entropy pass never double-flags or corrupts a match.

## The bug I did not expect

Late in the project I piped some output into `head` and got a Python traceback. A tool built to
live in a pipe was crashing on the most normal thing a pipe does: the reader downstream closing
early. That is a `BrokenPipeError`, and `cat`, `grep`, and `sed` all handle it silently. Safelog
now catches it, points stdout at `/dev/null` so the interpreter's final flush stays quiet, and
exits like any signalled pipe member. It is a small fix, but it is the kind of thing that separates
a script from a tool.

## What I would do differently

I would design the config format last, not in the middle. I hand-wrote a tiny TOML-subset parser
to keep the zero-dependency promise across Python 3.9 (where `tomllib` does not exist yet), and it
works, but I could have shipped the whole detector and streaming core first and bolted config on
once the shape was obvious.

The whole thing is standard library only, short enough to read before you trust it, and MIT
licensed.

- Live site: https://apps.charliekrug.com/safelog
- Source: https://github.com/ctkrug/safelog

If you pipe logs into an AI agent too, I would like to know what secret shapes you have seen leak
that Safelog does not catch yet.
