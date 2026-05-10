# alaska-ai-weekly

Source for the **Alaska.Ai Weekly FB Post** Claude Code Routine.

Every Saturday at 5:00 AM AK time, a Claude routine cloned from this repo:

1. Spawns five parallel research subagents covering different beats of AI/robotics in Alaska.
2. Validates every story (URLs resolve, dates in window, sourcing rule).
3. Selects the lead + 2-4 supporting stories.
4. Drafts the post in the analytical, position-taking voice anchored on `examples/post_001.md`.
5. Runs an editor + scorer loop until the post hits the rubric threshold.
6. Renders a 1080x1350 brand image via the `alaska-ai-brief` skill.
7. Drops a polished HTML draft in your connected Gmail with the post text + image inline.
8. Commits all artifacts to a `claude/weekly-{YYYY-MM-DD}` branch.

## Setup

1. Push this repo to GitHub.
2. Open https://claude.ai/code/routines and create a new routine bound to this repo.
3. Configure: model = Opus, network = Trusted, connectors = Gmail, schedule = Weekly Saturday 5am America/Anchorage.
4. Paste the prompt from `prompts/routine_instructions.md` into the Instructions field.
5. Set `launch_date` in `config/state.yaml` to the Saturday VOL. 01 ships.
6. Click **Run now** for a smoke test before the first scheduled run.

## Local smoke test of the image renderer

```bash
pip install -r requirements.txt
mkdir -p out
python .claude/skills/alaska-ai-brief/build_template.py \
  --volume "VOL. 01" \
  --topic  "The Federal AI Push\nHits The 49th" \
  --date   "10 MAY 2026" \
  --byline "BY TALON" \
  --kicker "WEEKLY BRIEF" \
  --out    out/post_image.png
open out/post_image.png   # macOS; use xdg-open on Linux
```

A sidecar `out/post_image.png.meta.json` is written next to the PNG.

## What the routine does NOT do

- Render the cover photo (static, manually uploaded).
- Render the profile photo (static, manually uploaded).
- Post directly to Facebook (you copy/paste from the Gmail draft).

## Files of note

- `prompts/routine_instructions.md` — the pasted routine prompt.
- `.claude/skills/alaska-ai-brief/` — the brand image generator.
- `.claude/agents/*.md` — subagent definitions.
- `config/brand.yaml` — voice anchor.
- `examples/post_001.md` — published style baseline.
- `config/scoring_rubric.yaml` — ship threshold.
