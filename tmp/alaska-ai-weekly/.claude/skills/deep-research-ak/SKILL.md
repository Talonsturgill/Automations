---
name: deep-research-ak
description: Orchestration recipe for the Alaska AI weekly deep-research pass. Used by the routine orchestrator and by the researcher subagents. Includes search-query templates per beat, credibility ranks, and a drop list.
---

# Deep research — Alaska AI

A short reference for the 7-day research pass.

## Search query templates

For each beat, run at minimum these query shapes:

- `"Alaska" "<beat keyword>" 2026`
- `site:<seed-source> "<beat keyword>"`
- `"<AK org name>" AI` for: UAF, UAA, APU, Sealaska, Calista, NANA, Doyon, ASRC, BBNC, Bristol Bay, AIDEA, NOAA Alaska, USGS Alaska, DEC, ADF&G
- `"<AK place>" AI` for: Anchorage, Fairbanks, Juneau, Bethel, Nome, Kodiak, Utqiagvik, Sitka, Wasilla
- `"data center" Alaska` (Beat A specifically)
- `"Cook Inlet" gas AI` (Beat A — energy supply story)
- `"JBER" OR "Eielson" OR "Clear SFS" AI` (Beats C / E — defense)

## Credibility ranks (used in `confidence`)

- **Primary** — agency, university, tribal corp, company first-party announcement.
- **High** — AK desk reporters at ADN / APM / Alaska Beacon / KTOO / KNBA; national wires (AP, Reuters); NYT / WaPo / Bloomberg desk reporters covering the story directly.
- **Medium** — local TV, regional trade publications, op-eds in credible outlets.
- **Low** — blogs, social posts, opinion aggregators. Use only as discovery, never as sole sourcing.

## Drop list — don't cite

- Press-release aggregators with no editorial layer.
- Sponsored content (look for "Sponsored" / "Partner content" labels).
- LinkedIn posts as primary sourcing (use only as a tip to find a real source).
- Anything paywalled where you couldn't read the body.

## Discovery surface

When you find a credible source not in `config/sources.yaml`, return it under `new_sources_to_consider` with a one-line rationale. The repo maintainer promotes good ones into the seed list weekly.
