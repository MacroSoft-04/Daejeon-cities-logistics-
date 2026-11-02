"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/tradedata_dj_2020_2025.csv (관세청 무역통계)
* Chart: exports above the axis, imports below, stacked by commodity group,
  with the trade balance drawn on the same scale. Splitting these into two
  charts hid the fact that the two sides are driven by different commodities.
* Grouping: the two flows are collapsed into one shared set of four groups.
  Ranking each side separately would put different commodities in the same
  colour and make the panels uncomparable.
* Output: output/02_trade_diverging.jpg
====================================================================
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
from core.utils_chart import PALETTE, PALETTE_CYCLE, save, use_korean_font

data_dir = BASE_DIR / "data" / "processed"
FILE_PATH = data_dir / "tradedata_2000_2025_4_added.csv"

MILLION = 1_000  # source unit is thousand USD
LABEL_MIN_SHARE = 0.15

use_korean_font()

df = pd.read_csv(FILE_PATH)
ratio_col = {"수출금액": "수출비율", "수입금액": "수입비율"}


def plot_trade_detail():
    """Plot exports above the axis, imports below, stacked by commodity group,
    with the trade balance drawn on the same scale.
    """
    exports = df[df["부명약칭"] == "기계 및 전기기기"]
    imports = df[df["부명약칭"] == "광물성 생산품"]
    print(exports)
    print(imports)
    years = exports.index.tolist()
    x = np.arange(len(years))
    width = 0.6

    # The balance line crossed the stacks when drawn on the same axes, so it gets
    # its own panel sharing the x axis.
    fig, ax = plt.subplots(figsize=(12, 9), sharex=True)

    groups = ["기계 및 전기기기", "광물성 생산품"]
    seen_labels = set()

    for frame, groups, sign in (
        (exports, ["기계 및 전기기기"], 1),
        (imports, ["광물성 생산품"], -1),
    ):
        totals = frame.sum(axis=1)
        bottom = np.zeros(len(years))

        for section in groups:
            values = frame[section].to_numpy(dtype=float) / MILLION * sign
            label = section if section not in seen_labels else None
            seen_labels.add(section)
            ax.bar(
                x,
                values,
                bottom=bottom,
                width=width,
                color=PALETTE_CYCLE[len(ax.patches) % len(PALETTE_CYCLE)],
                edgecolor="white",
                linewidth=0.8,
                label=label,
            )
            for xi, (value, base) in enumerate(zip(values, bottom)):
                share = frame[section].iloc[xi] / totals.iloc[xi]
                if share < LABEL_MIN_SHARE:
                    continue
                ax.text(
                    xi,
                    base + value / 2,
                    f"{share * 100:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=PALETTE["text"] if section == "기타" else "white",
                )
            bottom += values

    ax.axhline(0, color="#1c1c1c", linewidth=1.2)
    ax.set_ylabel("금액 (백만 USD)")
    # Values below the axis are import volumes, not negative amounts.
    ax.yaxis.set_major_formatter(lambda value, _: f"{abs(value):,.0f}")
    ax.set_title(
        "대전 수출입 구조",
        fontsize=15,
        fontweight="bold",
        pad=16,
    )
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    ax.legend(
        bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False, title="품목 구분"
    )

    span = ax.get_ylim()
    ax.text(
        -0.62, span[1] * 0.9, "수출 ▲", fontsize=11, fontweight="bold", color="#2c3e50"
    )
    ax.text(
        -0.62, span[0] * 0.9, "수입 ▼", fontsize=11, fontweight="bold", color="#2c3e50"
    )

    fig.text(
        0.5,
        -0.01,
        f"막대 안 숫자는 각 흐름 내 비중 ({LABEL_MIN_SHARE * 100:.0f}% 미만 생략) | "
        "자료: 관세청 무역통계",
        ha="center",
        fontsize=8,
        color="#7a848d",
    )
    save(fig, "TD_3_Daejeon_trade_detail.jpg")


plot_trade_detail()
