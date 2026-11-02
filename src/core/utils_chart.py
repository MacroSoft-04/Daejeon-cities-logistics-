"""
====================================================================
* Author: Minseo Kim
* Purpose: Shared figure styling so every chart in the project reads as
  one set, and Korean labels render on whichever machine runs the code.
====================================================================
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "output"

# Ordered by preference; the first installed family wins so the same script
# renders on Windows, macOS and Linux without edits.
KOREAN_FONTS = [
    "Malgun Gothic",
    "AppleGothic",
    "NanumGothic",
    "Noto Sans CJK KR",
    "Noto Sans CJK JP",
]

PALETTE = {
    "primary": "#2b5c8f",
    "accent": "#e74c3c",
    "muted": "#9aa5b1",
    "positive": "#2b7a5c",
    "negative": "#c0563f",
    "text": "#2c3e50",
    "1": "#3498db",
    "2": "#fcbc44",
    "3": "#9bd439",
    "4": "#9b59b6",
}

PALETTE_CYCLE = {
    0: PALETTE["1"],
    1: PALETTE["2"],
    2: PALETTE["3"],
    3: PALETTE["4"],
}


def use_korean_font() -> str:
    available = {f.name for f in font_manager.fontManager.ttflist}
    family = next((f for f in KOREAN_FONTS if f in available), None)
    if family is None:
        raise RuntimeError(f"No Korean font found. Install one of: {KOREAN_FONTS}")

    plt.rc("font", family=family)
    plt.rc("axes", unicode_minus=False)
    plt.rc("axes", edgecolor="#d7dbe0", labelcolor=PALETTE["text"])
    plt.rc("text", color=PALETTE["text"])
    plt.rc("xtick", color=PALETTE["text"])
    plt.rc("ytick", color=PALETTE["text"])
    return family


def save(fig, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved: {path}")
