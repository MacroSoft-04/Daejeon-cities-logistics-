"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/tradedata_2000_2025_4_added.csv (관세청 무역통계)
* Chart: section shares of exports and imports for Daejeon, the nation and
  the Chungcheong region, averaged over the last N years. A dot plot is used
  instead of grouped bars because the point is the gap between regions for
  the same section, which dots on one line show directly.
* Combining regions: 충남(세종 포함) and 충북 amounts are summed before shares
  are computed, so the larger province is weighted by its actual trade.
* Output: output/TD_11_section_share_compare.png
          output/TD_11_section_share_compare.csv
====================================================================
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.ticker as ticker
import math

SRC_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
from core.utils_chart import PALETTE, TRADE_DATA, save, use_korean_font

data_dir = BASE_DIR / "data" / "processed"
FILE_PATH = data_dir / "tradedata_2000_2025_4_added.csv"

MILLION = 1_000  # source unit is thousand USD
LABEL_MIN_SHARE = 15

REGION = ["대전광역시", "전국", "충청남도(세종특별자치시 포함)", "충청북도"]

COLORS = {
    "대전광역시": PALETTE["primary"],
    "전국": PALETTE["muted"],
    "충청남도(세종특별자치시 포함)": PALETTE["3"],
    "충청북도": PALETTE["2"],
}

FLOWS = {"수출금액": "수출", "수입금액": "수입"}
MIN_WEIGHT = 1

SAVE = "TD_11_section_share_compare.png"

use_korean_font()

df = pd.read_csv(FILE_PATH)
df = df[df["지역명"].isin(REGION)].copy()

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def sections_check(flow: str) -> tuple[int, pd.DataFrame, list]:
    """Find the top commodity groups over the past 10 years based on average sectional import and export values."""
    start = df["기간"].max() - 9
    frame = df[df["기간"].ge(start)]
    grouped = frame.groupby(
        ["지역명", "기간", "부명약칭"],
        as_index=True,
    )[list(FLOWS)].sum()

    year = grouped.unstack(level="부명약칭", fill_value=0)
    totals = year.T.groupby(level=0).transform("sum").T
    shares = year.div(totals)
    average = shares.groupby(level="지역명").mean() * 100

    chapters = set()
    for region in REGION:
        for cost, flow in FLOWS.items():
            values = average.loc[region, cost]
            top5 = values.nlargest(5)

            debug_print(f"\n{region}: {flow} ({start}~{df['기간'].max()}):")
            debug_print(top5.to_string())
            chapters.update(top5.index)
    chapters = list(chapters)
    debug_print(f"\n{chapters}")
    filtered = average.loc[:, average.columns.get_level_values(1).isin(chapters)]
    return start, filtered, chapters


def plot():
    """Plot exports above the axis, imports below, stacked by commodity group."""
    start, table, chapters = sections_check(df)
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(17, 6),
        sharey=True,
        layout="constrained",
    )
    y = np.arange(len(chapters))

    for ax, (cost, flow) in zip(axes, FLOWS.items()):
        all_values = []
        for region in REGION:
            values = table.loc[region, cost].reindex(chapters)
            x = values.to_numpy()
            all_values.append(x)
            ax.scatter(x, y, s=40, c=COLORS[region], label=region)

            ax.set_title(flow, loc="left", fontsize=10, fontweight="bold")
            ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")

            ax.set_yticks(y, chapters)

            ax.grid(linestyle="--", color="grey", linewidth=0.5, alpha=0.5)

        all_values = np.array(all_values)
        xmin = np.nanmin(all_values, axis=0)
        xmax = np.nanmax(all_values, axis=0)
        ax.hlines(y, xmin, xmax, color="#1c1c1c", linewidth=1, alpha=0.5)

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            title="권역",
            loc="upper right",
            frameon=False,
            bbox_to_anchor=(1, 1.03),
            fontsize=10,
            title_fontsize=11,
        )

        plt.tight_layout(rect=[0, 0.03, 0.90, 0.95])
        ax.set_xlabel(f"지역 {flow} 중 비중 (%)", fontsize=11)
        ax.set_ylabel("")

    fig.suptitle(
        f"대전·전국·충남·충북 부별 수출입 비중 ({start}~{df['기간'].max()} 연평균)",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, SAVE)


if __name__ == "__main__":
    plot()
