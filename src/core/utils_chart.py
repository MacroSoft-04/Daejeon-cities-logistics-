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
    "1": "#6F8FAF",
    "2": "#40B5AD",
    "3": "#9FE2BF",
    "4": "#59a11e",
    "5": "#008080",
    "6": "#6d8bef",
    "7": "#CCCCFF",
}

TRADE_DATA = {
    "기계 및 전기기기": PALETTE["primary"],
    "수송기기": PALETTE["1"],
    "광학, 정밀, 의료기기": PALETTE["2"],
    "조제식품류": PALETTE["3"],
    "화학공업 제품": PALETTE["4"],
    "광물성 생산품": PALETTE["5"],
    "플라스틱 및 고무 제품": PALETTE["6"],
    "비금속 및 그 제품": PALETTE["7"],
    "기타": PALETTE["muted"],
}

TRADE_DATA_SECTION = {
    "전기기기": PALETTE["primary"],
    "기계류": PALETTE["1"],
    "각종_화학공업생산품": PALETTE["2"],
    "향료_화장품": PALETTE["3"],
    "유기화학품": PALETTE["4"],
    "무기화학품": PALETTE["5"],
    "각종_화학공업생산품": PALETTE["6"],
    "의료용품": PALETTE["7"],
    "기타": PALETTE["muted"],
}

# core/trade_combine.py
import pandas as pd

HS_KEYS = ["기간", "부코드", "부명약칭", "류코드", "류명약칭"]
SUM_COLUMNS = ["수출건수", "수출금액", "수입건수", "수입금액", "무역수지"]


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
