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
from core.utils_chart import DEVICE_FOOD, save, use_korean_font

data_dir = BASE_DIR / "data" / "processed"
FILE_PATH = data_dir / "tradedata_2000_2025_4_added.csv"

MILLION = 1_000  # source unit is thousand USD
LABEL_MIN_SHARE = 15

DOMINANT = {
    "조제식품류": ["담배", "사료"],
    "광학, 정밀, 의료기기": ["광학_정밀의료기기"],
}
FLOWS = {"수출금액": "수출", "수입금액": "수입"}

SECTION = list(dict.fromkeys(DOMINANT))

DJ = "대전광역시"

SAVE = "TD_09_DJ_food_medic_detail.png"

use_korean_font()

df = pd.read_csv(FILE_PATH)
df = df[df["지역명"].eq(DJ) & df["부명약칭"].isin(SECTION)].copy()

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def check_shares_detail_rank(df: pd.DataFrame) -> dict:
    """Find the top chapter over the past 10 years based on average sectional import and export values."""
    start = df["기간"].max() - 9
    frame = df[df["기간"].gt(start)]
    for section in SECTION:
        section_frame = frame[frame["부명약칭"].eq(section)]
        year = section_frame.groupby(["류명약칭", "기간"], as_index=False)[
            ["수출금액", "수입금액"]
        ].sum()
        ex_ratio = year.groupby("류명약칭")["수출금액"].mean()
        im_ratio = year.groupby("류명약칭")["수입금액"].mean()

        debug_print(f"\n--- {section} ---")
        debug_print("\nExport Rank(2016~2025):")
        debug_print(ex_ratio.nlargest().to_string())
        debug_print("\nImport Rank(2016~2025):")
        debug_print(im_ratio.nlargest().to_string())
    return


def dominant_shares(frame):
    """Percent of each section's recent total held by its dominant chapters, per flow"""
    start = df["기간"].max() - 9
    frame = df[df["기간"].gt(start)]
    rows = {}
    for section, chapters in DOMINANT.items():
        part = frame[frame["부명약칭"].eq(section)]
        group = part["류명약칭"].where(part["류명약칭"].isin(chapters), "기타")
        for cost, flow in FLOWS.items():
            totals = (
                part.groupby(group)[cost]
                .sum()
                .reindex(chapters + ["기타"], fill_value=0)
            )
            rows[f"{section} {flow}"] = totals / totals.sum() * 100
    return pd.DataFrame(rows).T.fillna(0), start


def plot_regions():
    """Plot exports above the axis, imports below, stacked by commodity group."""
    table, start = dominant_shares(df)
    fig, ax = plt.subplots(
        figsize=(11, 0.7 * len(table) + 1.5),
        layout="constrained",
    )
    left = np.zeros(len(table))
    y_positions = np.arange(len(table))
    for group in table.columns:
        values = table[group].to_numpy()
        ax.barh(
            list(table.index),
            values,
            left=left,
            color=DEVICE_FOOD[group],
            edgecolor="white",
        )
        for row, value, base, share in zip(y_positions, values, left, table[group]):
            if share < LABEL_MIN_SHARE:
                continue
            ax.text(
                base + value / 2,
                row,
                f"{group}\n{share:.0f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if group != "기타" else "#2c3e50",
            )
        left += values
    ax.xaxis.set_major_formatter(lambda v, _: f"{abs(v):.0f}%")

    fig.suptitle(
        f"대전광역시 조제식품류·광학·정밀·의료기기 수출입 류별 구성 ({start}~{df['기간'].max()} 누적)",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, SAVE)


if __name__ == "__main__":
    plot_regions()
