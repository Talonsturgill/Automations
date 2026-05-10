"""Build the HTML body + base64 image payload for the weekly Gmail draft.

This script is invoked by the routine to compose the email pieces. The actual
draft creation happens via the Gmail MCP `create_draft` tool — this script
just returns a clean payload (JSON to stdout) the orchestrator passes through.

Note: Gmail MCP `create_draft` does not yet support attachments. The image
is embedded inline as a base64 `<img src="data:image/png;base64,...">` so
right-click → copy image works in Gmail. The same PNG is also committed to
the `claude/weekly-*` branch as a hosted fallback.

Usage:
  python scripts/gmail_draft.py \\
    --post-md out/final_post.md \\
    --image   out/post_image.png \\
    --sources out/source_ledger.json \\
    --score   out/score_report.json \\
    --date    2026-05-10 \\
    --branch  claude/weekly-2026-05-10
"""

import argparse
import base64
import datetime as dt
import json
from pathlib import Path

CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:#1a1a1a;background:#fafafa;margin:0;padding:24px;}
.wrap{max-width:720px;margin:0 auto;background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:28px;}
h1{font-size:22px;margin:0 0 4px;}
.sub{color:#666;font-size:13px;margin-bottom:24px;}
h2{font-size:16px;margin-top:28px;border-bottom:1px solid #eee;padding-bottom:6px;}
pre.post{white-space:pre-wrap;background:#f6f6f6;padding:16px;border-radius:8px;font-family:ui-monospace,Menlo,monospace;font-size:14px;line-height:1.5;}
.img{text-align:center;margin:18px 0;}
.img img{max-width:100%;height:auto;border-radius:8px;border:1px solid #e5e5e5;}
ul{padding-left:22px;} li{margin:4px 0;font-size:14px;}
table.score{width:100%;border-collapse:collapse;font-size:13px;}
table.score th,table.score td{border-bottom:1px solid #eee;padding:6px 8px;text-align:left;}
.foot{color:#888;font-size:11px;margin-top:22px;}
.flag{background:#fff4e5;border-left:3px solid #f0a500;padding:10px 12px;border-radius:4px;margin:14px 0;}
"""


def render(post_text, image_b64, sources, score, date_str, branch):
    src_items = "\n".join(
        f'<li><a href="{s["url"]}">{s["outlet"]}</a> &mdash; '
        f'{s.get("pub_date","")} &mdash; {s.get("story_title","")}</li>'
        for s in sources.get("sources", [])
    )
    score_rows = "\n".join(
        f'<tr><td>{c["name"]}</td><td>{c["score"]}</td>'
        f'<td>{c["weight"]}</td><td>{c.get("notes","")}</td></tr>'
        for c in score.get("criteria", [])
    )
    ship_flag = "" if score.get("ship") else (
        f'<div class="flag"><b>Below threshold.</b> Weakest: '
        f'{score.get("weakest_criterion","?")}. '
        f'Fix: {score.get("one_sentence_fix","?")}</div>'
    )
    return f"""<!doctype html><html><head><style>{CSS}</style></head><body>
<div class="wrap">
  <h1>Alaska.Ai &mdash; Weekly Recap Draft</h1>
  <div class="sub">{date_str} &middot; branch <code>{branch}</code></div>
  <h2>Copy this for Facebook</h2>
  <pre class="post">{post_text}</pre>
  <div class="img"><img src="data:image/png;base64,{image_b64}" alt="Alaska.Ai weekly image"/></div>
  {ship_flag}
  <h2>Sources</h2>
  <ul>{src_items}</ul>
  <h2>Editor's report card</h2>
  <table class="score">
    <tr><th>Criterion</th><th>Score</th><th>Weight</th><th>Notes</th></tr>
    {score_rows}
  </table>
  <p><b>Weighted total:</b> {score.get("weighted_total","?")} / 10 &middot;
     <b>Threshold:</b> {score.get("threshold","?")} &middot;
     <b>Ship:</b> {"yes" if score.get("ship") else "no &mdash; see flag above"}</p>
  <div class="foot">Generated {dt.datetime.utcnow().isoformat()}Z by the Alaska.Ai Weekly routine.</div>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-md", required=True)
    ap.add_argument("--image",   required=True)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--score",   required=True)
    ap.add_argument("--date",    required=True)
    ap.add_argument("--branch",  required=True)
    args = ap.parse_args()

    post_text = Path(args.post_md).read_text()
    image_b64 = base64.b64encode(Path(args.image).read_bytes()).decode("ascii")
    sources = json.loads(Path(args.sources).read_text())
    score = json.loads(Path(args.score).read_text())

    payload = {
        "subject": f"Alaska.Ai — Weekly Recap Draft — {args.date}",
        "to": "me",
        "html_body": render(post_text, image_b64, sources, score, args.date, args.branch),
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
