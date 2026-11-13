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
import matplotlib.ticker as ticker

SRC_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
from core.utils_chart import TRADE_DATA, save, use_korean_font

data_dir = BASE_DIR / "data" / "processed"
FILE_PATH = data_dir / "tradedata_2000_2025_4_added.csv"

MILLION = 1_000  # source unit is thousand USD
LABEL_MIN_SHARE = 15

DJ = "대전광역시"
NATIONAL = "전국"
TARGET = [DJ, NATIONAL]
MIN_WEIGHT = 1

SAVE = "TD_10_DJ_section_ratio_per_nation.png"

use_korean_font()

df = pd.read_csv(FILE_PATH)
df = df[df["지역명"].isin(TARGET)].copy()

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


daejeon = (
    df[df["지역명"].eq(DJ)]
    .groupby(["부명약칭", "류명약칭", "기간"], as_index=False)[["수출금액", "수입금액"]]
    .sum()
)

national = (
    df[df["지역명"].eq(NATIONAL)]
    .groupby(["부명약칭", "류명약칭", "기간"], as_index=False)[["수출금액", "수입금액"]]
    .sum()
)


target = pd.merge(
    daejeon,
    national,
    on=["부명약칭", "류명약칭", "기간"],
    suffixes=("_대전", "_전국"),
    validate="one_to_one",
)

target["전국대비_수출"] = target["수출금액_대전"] / target["수출금액_전국"] * 100
target["전국대비_수입"] = target["수입금액_대전"] / target["수입금액_전국"] * 100


def chapter_profile(target: pd.DataFrame) -> tuple[np.int64, pd.DataFrame, dict]:
    """Per chapter over the last 10 years: weight in 대전's trade and 대전's share of the national total."""
    start = target["기간"].max() - 9
    frame = target[target["기간"].ge(start)]
    totals = frame.groupby(["부명약칭", "류명약칭"], as_index=False)[
        ["수출금액_대전", "수입금액_대전", "수출금액_전국", "수입금액_전국"]
    ].sum()
    profile = pd.DataFrame(
        {
            "부명약칭": totals["부명약칭"],
            "류명약칭": totals["류명약칭"],
            "대전내_수출비중": totals["수출금액_대전"]
            / totals["수출금액_대전"].sum()
            * 100,
            "전국대비_수출": totals["수출금액_대전"] / totals["수출금액_전국"] * 100,
            "대전내_수입비중": totals["수입금액_대전"]
            / totals["수입금액_대전"].sum()
            * 100,
            "전국대비_수입": totals["수입금액_대전"] / totals["수입금액_전국"] * 100,
        }
    )
    baseline = {
        "수출_기준": totals["수출금액_대전"].sum()
        / totals["수출금액_전국"].sum()
        * 100,
        "수입_기준": totals["수입금액_대전"].sum()
        / totals["수입금액_전국"].sum()
        * 100,
    }
    label = f"{start}~{target['기간'].max()}"
    relevant = profile[
        profile[f"대전내_수출비중"].ge(MIN_WEIGHT)
        | profile[f"대전내_수입비중"].ge(MIN_WEIGHT)
    ].round(1)
    for flow in ("수출", "수입"):
        check = profile[profile[f"대전내_{flow}비중"].ge(MIN_WEIGHT)]
        debug_print(
            f"\n{flow} rank by national({label}, proportion within Daejeon >= 1%)"
        )
        debug_print(check.nlargest(5, f"전국대비_{flow}").to_string())
    return start, relevant, baseline


def plot_profile():
    """Plot exports above the axis, imports below, stacked by commodity group."""
    start, table, baseline = chapter_profile(target)
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(17, 6),
        layout="constrained",
    )
    axes[1].xaxis.set_major_locator(ticker.MultipleLocator(5))
    handles, labels = {}, {}
    for flow, ax in zip(("수출", "수입"), axes):
        x_col, y_col = f"대전내_{flow}비중", f"전국대비_{flow}"
        main = table[table[x_col].ge(MIN_WEIGHT)]
        for chapter, group in main.groupby("부명약칭"):
            for h, l in zip(*ax.get_legend_handles_labels()):
                handles.setdefault(l, h)
            ax.scatter(
                group[x_col],
                group[y_col],
                s=40,
                color=TRADE_DATA.get(chapter, TRADE_DATA["기타"]),
                label=chapter,
            )
            for xi, yi, name in zip(group[x_col], group[y_col], group["류명약칭"]):
                ax.annotate(
                    name,
                    (xi, yi),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=7,
                )

        ax.set_title(flow, loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel(f"대전 {flow} 중 비중 (%)", fontsize=11)
        ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")

        ax.set_yscale("log")
        ax.set_yticks([0.01, 0.1, 1, 10])
        ax.set_yticklabels(["0.01", "0.1", "1", "10"])
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}%")
        ax.set_ylabel(f"전국 {flow} 대비 대전 비중 (%, 로그)", fontsize=11)

        ax.grid(linestyle="--", color="grey", linewidth=0.5, alpha=0.5)

        ax.axhline(y=baseline[f"{flow}_기준"], color="red", linestyle="--", linewidth=1)
        ax.annotate(
            f"대전 전체 {baseline[f'{flow}_기준']:.1f}%",
            (1, baseline[f"{flow}_기준"]),
            xycoords=("axes fraction", "data"),
            ha="center",
            va="bottom",
            color="red",
            fontsize=10,
        )

        plt.tight_layout(rect=[0, 0.03, 0.90, 0.95])  # reserve room on the right
    fig.legend(
        handles.values(),
        handles.keys(),
        loc="outside upper center",
        ncol=5,
        frameon=False,
        fontsize=10,
        bbox_to_anchor=(0.5, 0.94),
    )
    fig.suptitle(
        f"대전광역시 류별 수출입의 지역 내 비중과 전국 대비 비중 ({start}~{df['기간'].max()} 누적)",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, SAVE)


if __name__ == "__main__":
    plot_profile()
