# Safelog — Design

Safelog ships as a CLI, so "the page" is its marketing landing page (`site/index.html`). This
doc is the single source of truth for how that page looks. Product and page are one brand.

## 1. Aesthetic direction

**Terminal-mono with a redaction motif.** The page looks like the place Safelog lives: a dark
terminal, monospace type, a live stream of log lines where secrets flip to black-bar
`[REDACTED:...]` placeholders. The signature interaction *is* the product doing its job.

Chosen over a generic "dark cards + one accent" dev-tool layout because Safelog has a literal
visual: the redaction bar. Leaning into it gives the page a memorable, on-brand hero instead of a
stock feature grid.

## 2. Tokens (actual values)

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0a0e14` | page background (deep ink, never pure black) |
| `--surface-1` | `#111722` | terminal / card body |
| `--surface-2` | `#18202e` | raised rows, code blocks |
| `--border` | `#243044` | hairlines |
| `--text` | `#e6edf3` | body text |
| `--muted` | `#8b98a5` | secondary text, captions |
| `--accent` | `#4ade80` | phosphor green: wordmark glyph, links, primary CTA, `[REDACTED]` bars |
| `--accent-dim` | `#22c55e` | pressed / hover green |
| `--support` | `#fbbf24` | amber: the secret *before* it gets redacted (the flash) |
| `--danger` | `#f87171` | reserved for error copy |

- **Type pairing:** display/mono = **JetBrains Mono** (wordmark, headings, terminal, code); UI =
  **Inter** (body copy, FAQ). System fallbacks: `ui-monospace, SFMono-Regular, Menlo` and
  `system-ui, -apple-system, sans-serif`.
- **Type scale:** ~1.25 ratio. Body 16px, small 13px.
- **Spacing:** 8px scale (8 / 16 / 24 / 32 / 48 / 64).
- **Radius:** 10px cards, 6px inline chips.
- **Depth:** layered shadows (`0 1px 0 rgba(255,255,255,.03) inset, 0 12px 40px rgba(0,0,0,.5)`)
  plus a soft green glow on the primary CTA. Background gets a radial gradient + faint scanline
  texture + vignette, never a flat fill to the edges.
- **Motion:** UI transitions 160-220ms ease-out; the redaction wipe ~450ms; the wordmark cursor
  blinks at 1.1s.

## 3. Layout intent

The **hero terminal is the hero** (~60% of the viewport on desktop). Left column: wordmark,
headline, subhead, install one-liner, primary CTA. Right column (stacks under on phone): a
terminal window that streams real-looking log lines and redacts the secrets in them on a loop.
Below the fold: a benefits row, a real before/after sample, install + usage, and the FAQ. Composed
and gap-free at 390px, 768px, and 1440px with no horizontal scroll.

## 4. Signature detail

The **live redaction animation**: log lines type into the hero terminal; when a line contains a
secret, the secret flashes amber for a beat, then a green-edged black bar wipes across it left to
right and it settles as `[REDACTED:<name>]`. Loops. Honors `prefers-reduced-motion` by rendering
the already-redacted lines statically with no wipe or flash.

## 5. Brand assets

- **Favicon:** inline SVG data-URI, a terminal prompt glyph (`>_`) in accent green on the ink
  background. No default globe.
- **Wordmark:** `safelog` set in JetBrains Mono, with a blinking green block cursor after it and
  the accent used on the `>` prompt glyph.
