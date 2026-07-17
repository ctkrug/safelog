# Security Policy

Safelog exists to keep secrets out of places they shouldn't be, so we take security issues in the
tool itself seriously — especially anything that would let a real secret pass through undetected.

## Reporting a vulnerability

Please **do not open a public GitHub issue** for security reports. Instead, email
ctkrug4501@gmail.com with:

- A description of the issue and its impact (e.g., a secret shape that bypasses every detector).
- Steps to reproduce, ideally a minimal input line that demonstrates the gap.
- Your assessment of severity, if you have one.

You should expect an acknowledgement within a few days. Once a fix is available, it will be
released and noted in [`CHANGELOG.md`](CHANGELOG.md); credit is given unless you'd prefer
otherwise.

## Scope

In scope: detector bypasses, redaction logic that leaks a secret it claims to have redacted, and
any code execution or resource-exhaustion issue triggerable by piping crafted input through
`safelog`. Out of scope: secrets that were already exposed before reaching safelog, or detection
gaps for secret formats not yet listed in [`docs/BACKLOG.md`](docs/BACKLOG.md) (file those as
normal feature requests instead).
