---
name: alaska-ai-brief
description: Generate the Alaska.Ai weekly brief post graphic — a 1080x1350 portrait PNG with the locked Alaska.Ai brand design tokens (state-flag gold, aurora wash, Polaris star, Fraunces Black headline, JetBrains Mono telemetry). Use whenever creating the visual header for a new weekly Alaska AI news brief that will be posted to the Alaska.Ai Facebook page or other social surfaces (Instagram, LinkedIn, Substack header). Parameterized for volume, topic (quotable headline), date, byline, kicker.
---

# Alaska.Ai Weekly Brief Template

Generate the Alaska.Ai weekly brief post graphic. Use when creating the visual header for a new weekly Alaska AI news brief that will be posted to the Alaska.Ai Facebook page or other social surfaces (Instagram, LinkedIn, Substack header). Outputs a 1080x1350 portrait PNG using the locked Alaska.Ai brand design tokens. Parameterized for volume number, topic title, date, and byline.

## When to use

Trigger this skill whenever Talon writes "weekly brief", "Alaska.Ai post graphic", "brief header", "next issue", or similar language indicating a new entry in the weekly brief series. Also triggers on any request to generate a post header for the Alaska.Ai brand specifically.

Do NOT use for:
- The Facebook cover photo (that's a separate one-off asset, see `alaska-ai-cover` if it exists)
- The profile picture (also a separate asset)
- Generic post graphics for other Talon brands or projects

## Inputs (CLI args, all optional, sensible defaults)

- `--volume` Volume number string. Default `VOL. 01`. Examples `VOL. 02`, `VOL. 14`.
- `--topic` Topic title / quotable headline. Use `\n` for line break. Default `The Federal AI Push\nHits The 49th`. Keep to 1-2 lines, max ~28 chars per line for legibility at the locked 96px display size.
- `--date` Date stamp. Default `10 MAY 2026`. Format day-month-year all caps.
- `--byline` Byline credit. Default `BY TALON`.
- `--kicker` Kicker label above the headline. Default `WEEKLY BRIEF`. Can be swapped for `DEEP DIVE`, `FIELD NOTES`, `SPECIAL ISSUE`, etc.
- `--motto` Italic gold motto under the headline. Default `what's moving in alaska ai, this week`.
- `--coords` Footer coordinates stamp. Default `61°13′N  ·  149°54′W` (Anchorage).
- `--seed` Random seed for aurora + starfield. Default `11`. Same seed = same render.
- `--out` Output PNG path. Default `./alaska-ai-brief-{vol_slug}.png` derived from volume number.

## Locked design tokens (do not alter without rebrand approval)

```
SKY_TOP        rgb(2, 6, 20)     deep night sky
SKY_HORIZ      rgb(8, 20, 44)    flag-blue at horizon
FLAG_GOLD      rgb(255, 199, 44) Pantone 1235, Alaska state flag gold
FLAG_GOLD_HALO rgb(255, 218, 110) gold halo for stars and glows
FORGETMENOT    rgb(110, 165, 255) state flower blue, accent only

AURORA cyan-green   rgb(60, 230, 180)
AURORA cyan-blue    rgb(90, 200, 240)
AURORA violet       rgb(150, 100, 230)

DISPLAY FONT  Fraunces variable, opsz=144 wght=900 (Black) for headlines
ITALIC FONT   Fraunces Italic variable, opsz=12 wght=400 SOFT=50
MONO FONT     JetBrains Mono Regular for telemetry stamps
```

## Composition spec

- Canvas 1080x1350 (4:5 portrait, modern FB feed standard, max mobile real estate)
- Polaris gold star at top center, y=180, radius=34
- ALASKA.AI wordmark in Fraunces Black 64pt, white, top
- Kicker line in JetBrains Mono Medium 18pt, gold @ 80%, format `KICKER · VOL · DATE`
- Thin 120px gold rule beneath kicker
- Topic headline in Fraunces Black, **auto-shrink from 96pt → 64pt** to fit canvas width
- Italic gold motto beneath headline
- Footer band at y=H-110 with byline left, coordinates right
- Coordinates stamp `61°13′N · 149°54′W` (Anchorage default, overridable)
- Thin gold hairline above footer

## Soft aurora wash + starfield

- 3 aurora layers (cyan-green, cyan-blue, violet) with vertical bell + horizontal noise + heavy gaussian blur
- Intensity max 105 per layer (softer than cover, doesn't fight headline legibility)
- 180 stars in upper 50% of canvas, varying brightness, brightest get 4-pixel halos
- `--seed` controls aurora + star placement deterministically

## Dependencies

- Python 3.11+
- pillow, numpy, scipy
- Fraunces variable font (TTF), Fraunces Italic variable (TTF)
- JetBrains Mono Regular + Medium (TTF)

The build script auto-downloads fonts to `./fonts/` (relative to the script) on first run if missing. Cached after that by the environment snapshot.

## How to invoke from a Claude Code routine

```bash
python .claude/skills/alaska-ai-brief/build_template.py \
  --volume "VOL. 02" \
  --topic "Cook Inlet Gas Crunch\nWill Define Year One" \
  --date "17 MAY 2026" \
  --byline "BY TALON" \
  --kicker "WEEKLY BRIEF" \
  --out "out/post_image.png"
```

A sidecar `out/post_image.png.meta.json` is written next to the PNG with the render parameters and timestamp.

## Output

A 1080x1350 PNG. Roughly 180-220 KB. Sharp on retina. Drops cleanly into Facebook feed (4:5 portrait, max mobile presence) and Instagram (same ratio).

## Cross-platform notes

- Facebook native upload only. Do not attach as a link preview.
- For LinkedIn header use, generate a 1584x396 horizontal version (separate skill, not this one).
- For Instagram cross-post, this same 1080x1350 works directly.
- For Substack header inside the post, use as-is.

## When the brand evolves

If brand tokens change (new accent color, new font, new motto), update this SKILL.md AND the build_template.py constants in lockstep. Do not let token drift between the cover, profile, and brief template.
