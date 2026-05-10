"""
Alaska.Ai Weekly Brief — post graphic renderer.

Produces a 1080x1350 portrait PNG using the locked Alaska.Ai brand design
tokens. Parameterized for the variables that change weekly: volume, topic,
date, byline, kicker. See SKILL.md for full spec.

Usage:
  python build_template.py                              # default test render
  python build_template.py --volume "VOL. 02" \\
    --topic "Cook Inlet Gas Crunch\\nWill Define Year One" \\
    --date "17 MAY 2026" --byline "BY TALON" \\
    --out "./alaska-ai-brief-vol-02.png"

Dependencies:
  pip install pillow numpy scipy
  Fonts auto-download to ./fonts/ on first run.
"""

import argparse
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter

# ---------- canvas ----------
W, H = 1080, 1350
TOPIC_MARGIN_X = 80

# ---------- locked brand tokens (DO NOT ALTER without rebrand approval) ----------
SKY_TOP    = np.array([2,   6,  20], dtype=np.float32)
SKY_HORIZ  = np.array([8,  20,  44], dtype=np.float32)
FLAG_GOLD  = (255, 199, 44)
FLAG_GOLD_HALO = (255, 218, 110)
FORGETMENOT = (110, 165, 255)
WHITE = (255, 255, 255)

AURORA_BANDS = [
    np.array([60, 230, 180], dtype=np.float32),   # cyan-green
    np.array([90, 200, 240], dtype=np.float32),   # cyan-blue
    np.array([150, 100, 230], dtype=np.float32),  # violet
]

# ---------- font management ----------
SCRIPT_DIR = Path(__file__).parent.resolve()
FONTS_DIR = SCRIPT_DIR / "fonts"

FONT_URLS = {
    "Fraunces-Var.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/fraunces/"
        "Fraunces%5BSOFT%2CWONK%2Copsz%2Cwght%5D.ttf"
    ),
    "Fraunces-Italic-Var.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/fraunces/"
        "Fraunces-Italic%5BSOFT%2CWONK%2Copsz%2Cwght%5D.ttf"
    ),
    "JetBrainsMono-Regular.ttf": (
        "https://github.com/JetBrains/JetBrainsMono/raw/master/"
        "fonts/ttf/JetBrainsMono-Regular.ttf"
    ),
    "JetBrainsMono-Medium.ttf": (
        "https://github.com/JetBrains/JetBrainsMono/raw/master/"
        "fonts/ttf/JetBrainsMono-Medium.ttf"
    ),
}


def ensure_fonts():
    """Download fonts to ./fonts/ on first run."""
    FONTS_DIR.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        path = FONTS_DIR / name
        if not path.exists() or path.stat().st_size < 1000:
            print(f"Downloading {name}...", file=sys.stderr)
            try:
                urllib.request.urlretrieve(url, path)
            except Exception as e:
                print(f"  Failed to download {name}: {e}", file=sys.stderr)
                print(f"  Manually place at {path}", file=sys.stderr)
                sys.exit(1)
    return {
        "fraunces":     str(FONTS_DIR / "Fraunces-Var.ttf"),
        "fraunces_it":  str(FONTS_DIR / "Fraunces-Italic-Var.ttf"),
        "mono":         str(FONTS_DIR / "JetBrainsMono-Regular.ttf"),
        "mono_med":     str(FONTS_DIR / "JetBrainsMono-Medium.ttf"),
    }


# ---------- typography helpers ----------
def fraunces(size, weight=900, opsz=144, italic=False, soft=0, font_paths=None):
    """Load Fraunces with explicit variable axis settings."""
    path = font_paths["fraunces_it"] if italic else font_paths["fraunces"]
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes([opsz, weight, soft, 0])  # opsz, wght, SOFT, WONK
    except Exception:
        try:
            f.set_variation_by_axes([soft, 0, opsz, weight])
        except Exception:
            pass
    return f


def draw_tracked(d, text, font, fill, x, y, tracking_em=0.10):
    extra = int(round(font.size * tracking_em))
    cur = x
    for ch in text:
        d.text((cur, y), ch, font=font, fill=fill)
        bb = font.getbbox(ch)
        cur += (bb[2] - bb[0]) + extra
    return cur - extra


def measure_tracked(text, font, tracking_em=0.10):
    extra = int(round(font.size * tracking_em))
    total = 0
    for ch in text:
        bb = font.getbbox(ch)
        total += (bb[2] - bb[0]) + extra
    return total - extra


def fit_topic(lines, font_paths, max_width, sizes=(96, 88, 80, 72, 64)):
    """Auto-shrink: pick the largest size where every line fits max_width.
    Falls back to the smallest size on overflow (mild visual overflow possible
    but no crash)."""
    chosen = None
    for size in sizes:
        font = fraunces(size, weight=900, opsz=144, font_paths=font_paths)
        if all(measure_tracked(line, font, tracking_em=0.0) <= max_width for line in lines):
            return font, size
        chosen = (font, size)
    return chosen


# ---------- pipeline pieces ----------
def build_sky():
    sky = np.zeros((H, W, 3), dtype=np.float32)
    for y in range(H):
        t = (y / (H - 1)) ** 1.5
        sky[y] = SKY_TOP * (1 - t) + SKY_HORIZ * t
    return sky


def aurora_curtain(seed, vc, sp, hf, intensity, color, warp):
    rng = np.random.default_rng(seed)
    raw_x = rng.standard_normal(W)
    spine = gaussian_filter(raw_x, sigma=hf)
    spine = spine / (np.std(spine) + 1e-6) * warp
    streak_raw = rng.standard_normal((H, W))
    streak = gaussian_filter(streak_raw, sigma=(2.5, 28.0))
    streak = (streak - streak.min()) / (streak.max() - streak.min() + 1e-6)
    streak = streak ** 1.7
    ys = np.arange(H).reshape(-1, 1).astype(np.float32)
    spine_y = vc + spine.reshape(1, -1)
    bell = np.exp(-((ys - spine_y) ** 2) / (2 * sp ** 2))
    field = bell * streak * intensity
    field = gaussian_filter(field, sigma=(10, 14))
    return np.repeat(field[:, :, None], 3, axis=2) * (color / 255.0)


def add_aurora(sky, seed_base=11):
    layers = [
        (seed_base + 0,  H * 0.22,  80, 65, 105, AURORA_BANDS[0], 50),
        (seed_base + 12, H * 0.18,  50, 95,  95, AURORA_BANDS[1], 60),
        (seed_base + 26, H * 0.30, 100, 50,  75, AURORA_BANDS[2], 35),
    ]
    glow = np.zeros_like(sky)
    for s, vc, sp, hf, it, c, w in layers:
        glow += aurora_curtain(s, vc, sp, hf, it, c, w)
    return np.clip(sky + glow, 0, 255)


def add_stars(sky, seed=11):
    random.seed(seed)
    for _ in range(180):
        x = random.randint(0, W - 1)
        y = random.randint(0, int(H * 0.50))
        b = random.choice([35, 50, 65, 85, 110, 145])
        sky[y, x] = np.minimum(sky[y, x] + b, 255)
        if b > 95:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W:
                    sky[ny, nx] = np.minimum(sky[ny, nx] + b * 0.3, 255)
    return sky


def add_polaris(rgb_array, cx, cy, radius=34):
    img = Image.fromarray(rgb_array.astype(np.uint8)).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for r, alpha in [(radius * 5, 14), (radius * 3, 32), (radius * 1.8, 70)]:
        hd.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(*FLAG_GOLD_HALO, alpha))
    halo = halo.filter(ImageFilter.GaussianBlur(radius=radius * 0.7))
    layer.alpha_composite(halo)
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = radius if i % 2 == 0 else radius * 0.42
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    d.polygon(pts, fill=(*FLAG_GOLD, 255))
    d.ellipse([cx - radius * 0.25, cy - radius * 0.25,
               cx + radius * 0.25, cy + radius * 0.25],
              fill=(255, 240, 200, 255))
    return Image.alpha_composite(img, layer)


# ---------- main render ----------
def render(volume, topic, date, byline, kicker, out_path,
           coords="61°13′N  ·  149°54′W",
           motto="what's moving in alaska ai, this week",
           seed=11):
    fonts = ensure_fonts()

    sky = build_sky()
    sky = add_aurora(sky, seed_base=seed)
    sky = add_stars(sky, seed=seed)
    img = add_polaris(sky, cx=W // 2, cy=180, radius=34)
    draw = ImageDraw.Draw(img, "RGBA")

    # ALASKA.AI wordmark
    font_brand = fraunces(64, weight=900, opsz=144, font_paths=fonts)
    brand_text = "ALASKA.AI"
    bw = measure_tracked(brand_text, font_brand, tracking_em=0.06)
    draw_tracked(draw, brand_text, font_brand, (255, 255, 255, 255),
                 (W - bw) // 2, 250, tracking_em=0.06)

    # Kicker telemetry line
    font_mono_med = ImageFont.truetype(fonts["mono_med"], 18)
    kicker_text = f"{kicker}   ·   {volume}   ·   {date}"
    kw = measure_tracked(kicker_text, font_mono_med, tracking_em=0.20)
    draw_tracked(draw, kicker_text, font_mono_med, (*FLAG_GOLD, 200),
                 (W - kw) // 2, 350, tracking_em=0.20)

    # Gold rule under kicker
    rule_y = 395
    rule_w = 120
    draw.line([((W - rule_w) // 2, rule_y), ((W + rule_w) // 2, rule_y)],
              fill=(*FLAG_GOLD, 180), width=1)

    # Topic headline — auto-shrink to fit canvas width
    topic_lines = topic.split("\n")
    font_topic, topic_size = fit_topic(
        topic_lines, fonts, max_width=W - 2 * TOPIC_MARGIN_X
    )
    line_h = int(topic_size * 1.15)
    total_topic_h = line_h * len(topic_lines)
    topic_start_y = (H - total_topic_h) // 2 - 60
    for i, line in enumerate(topic_lines):
        lw = measure_tracked(line, font_topic, tracking_em=0.0)
        draw_tracked(draw, line, font_topic, (255, 255, 255, 255),
                     (W - lw) // 2, topic_start_y + i * line_h,
                     tracking_em=0.0)

    # Italic motto
    font_motto = fraunces(28, weight=400, opsz=14, italic=True, soft=50,
                          font_paths=fonts)
    mw = measure_tracked(motto, font_motto, tracking_em=0.10)
    motto_y = topic_start_y + total_topic_h + 30
    draw_tracked(draw, motto, font_motto, (*FLAG_GOLD, 210),
                 (W - mw) // 2, motto_y, tracking_em=0.10)

    # Footer
    footer_y = H - 110
    font_footer = ImageFont.truetype(fonts["mono"], 16)
    draw_tracked(draw, byline, font_footer, (255, 255, 255, 170),
                 64, footer_y, tracking_em=0.22)
    cw = measure_tracked(coords, font_footer, tracking_em=0.22)
    draw_tracked(draw, coords, font_footer, (255, 255, 255, 170),
                 W - 64 - cw, footer_y, tracking_em=0.22)

    # Hairline above footer
    draw.line([(64, footer_y - 24), (W - 64, footer_y - 24)],
              fill=(*FLAG_GOLD, 60), width=1)

    img.convert("RGB").save(out_path, "PNG", optimize=True)

    # Output validation — fail fast if dimensions are wrong
    verify = Image.open(out_path)
    if verify.size != (W, H):
        raise RuntimeError(
            f"output dimensions wrong: {verify.size} (expected {(W, H)})"
        )

    # Sidecar metadata for the audit trail
    meta = {
        "volume": volume,
        "topic": topic,
        "date": date,
        "byline": byline,
        "kicker": kicker,
        "motto": motto,
        "coords": coords,
        "seed": seed,
        "topic_font_size_used": topic_size,
        "rendered_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "canvas": [W, H],
        "out_path": str(out_path),
    }
    Path(str(out_path) + ".meta.json").write_text(json.dumps(meta, indent=2))

    return out_path


def main():
    p = argparse.ArgumentParser(
        description="Render Alaska.Ai weekly brief post graphic (1080x1350)."
    )
    p.add_argument("--volume", default="VOL. 01")
    p.add_argument("--topic",  default="The Federal AI Push\\nHits The 49th",
                   help="Topic headline. Use \\n for line breaks.")
    p.add_argument("--date",   default="10 MAY 2026")
    p.add_argument("--byline", default="BY TALON")
    p.add_argument("--kicker", default="WEEKLY BRIEF")
    p.add_argument("--motto",  default="what's moving in alaska ai, this week")
    p.add_argument("--coords", default="61°13′N  ·  149°54′W")
    p.add_argument("--seed",   type=int, default=11)
    p.add_argument("--out",    default=None)
    args = p.parse_args()

    topic = args.topic.replace("\\n", "\n")

    out = args.out
    if out is None:
        vol_slug = args.volume.lower().replace(" ", "").replace(".", "")
        out = f"./alaska-ai-brief-{vol_slug}.png"

    path = render(
        volume=args.volume,
        topic=topic,
        date=args.date,
        byline=args.byline,
        kicker=args.kicker,
        out_path=out,
        coords=args.coords,
        motto=args.motto,
        seed=args.seed,
    )
    print(f"Saved: {path}")
    print(f"Size:  {os.path.getsize(path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
