"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/tradedata_2000_2025_4_added.csv (관세청 무역통계)
* Chart: exports above the axis, imports below, stacked by commodity
  section, with the yearly trade balance in a separate panel below.
  Splitting exports and imports into two charts hid the fact that the
  two sides are driven by different sections.
* Grouping: top 4 sections per flow over the last 10 years, the rest as 기타.
  Colours come from TRADE_DATA, so a section has the same colour on both
  sides and in every chart.
* Tables: the README balance table (핵심 결과 2) is built from the same data
  in the same run, so the chart and the table cannot drift apart.
* Output: output/TD_2_Daejeon_trade_diverging.png
          output/TD_2_trade_balance_yearly.csv
          output/TD_2_trade_balance_periods.csv
====================================================================
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random

SRC_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
from core.utils_chart import PALETTE, TRADE_DATA, save, use_korean_font
from core.utils_trade_balance import period_table, yearly_balance, MILLION

data_dir = BASE_DIR / "data" / "processed"
FILE_PATH = data_dir / "tradedata_2000_2025_4_added.csv"
SAVE = "TD_2_Daejeon_trade_diverging.png"

LABEL_MIN_SHARE = 0.15

FOCUS = "대전광역시"
REGIONS = FOCUS, "전국"
THOUSAND_TO_MILLION = 1_000
TOP_N = 4
RANK_YEARS = 10
LABEL_MIN_SHARE = 0.15

use_korean_font()

df = pd.read_csv(FILE_PATH)
df = df[df["지역명"].eq(FOCUS)].copy()  # Filter for Daejeon

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


balance = df.groupby("기간")["무역수지"].sum() / MILLION

COLORS_BASIC = TRADE_DATA


def sections_check():
    """Find the top commodity groups over the past 10 years based on average sectional import and export values."""
    start = df["기간"].max() - 9
    frame = df[df["기간"].gt(start)]
    year = frame.groupby(["부명약칭", "기간"], as_index=False)[
        ["수출금액", "수입금액"]
    ].sum()
    ex_chap = year.groupby("부명약칭")["수출금액"].mean()
    im_chap = year.groupby("부명약칭")["수입금액"].mean()
    total = frame.groupby(["기간"], as_index=False)[["수출금액", "수입금액"]].sum()
    ex_total = total["수출금액"].mean()
    im_total = total["수입금액"].mean()
    ex_ratio = ex_chap / ex_total * 100
    im_ratio = im_chap / im_total * 100

    debug_print("\nExport Rank(2016~2025):")
    debug_print(ex_ratio.sort_values(ascending=False).to_string())
    debug_print("\nImport Rank(2016~2025):")
    debug_print(im_ratio.sort_values(ascending=False).to_string())

    EX_GROUPS = ex_ratio.nlargest(4).index.tolist()
    IM_GROUPS = im_ratio.nlargest(4).index.tolist()
    return EX_GROUPS, IM_GROUPS


def plot_trade_diverging():
    """Plot exports above the axis, imports below, stacked by commodity group,
    with the trade balance drawn on the same scale.
    """
    EX_GROUPS, IM_GROUPS = sections_check()
    df["ex_group"] = df["부명약칭"].where(df["부명약칭"].isin(EX_GROUPS), "기타")
    df["im_group"] = df["부명약칭"].where(df["부명약칭"].isin(IM_GROUPS), "기타")

    exports = (
        df.groupby(["기간", "ex_group"])["수출금액"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=EX_GROUPS + ["기타"], fill_value=0)
    )
    imports = (
        df.groupby(["기간", "im_group"])["수입금액"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=IM_GROUPS + ["기타"], fill_value=0)
    )
    balance = df.groupby("기간")["무역수지"].sum() / MILLION

    years = exports.index.tolist()
    x = np.arange(len(years))
    width = 0.6

    # The balance line crossed the stacks when drawn on the same axes, so it gets
    # its own panel sharing the x axis.
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(12, 9), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )

    COLORS = COLORS_BASIC.copy()
    seen_labels = set()

    for frame, plot_groups, sign in (
        (exports, EX_GROUPS + ["기타"], 1),
        (imports, IM_GROUPS + ["기타"], -1),
    ):
        totals = frame.sum(axis=1)
        bottom = np.zeros(len(years))

        for section in plot_groups:
            values = frame[section].to_numpy(dtype=float) / MILLION * sign
            label = section if section not in seen_labels else None
            seen_labels.add(section)
            ax.bar(
                x,
                values,
                bottom=bottom,
                width=width,
                color=COLORS[section],
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
                    color="#2c3e50" if section == "기타" else "white",
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

    bar_colors = [
        PALETTE["positive"] if v >= 0 else PALETTE["negative"] for v in balance
    ]

    ax2.bar(x, balance, width=width, color=bar_colors)
    ax2.axhline(0, color="#1c1c1c", linewidth=1.2)
    ax2.set_xticks(x)
    ax2.set_xticklabels(years)
    ax2.set_xlabel("연도")
    ax2.set_ylabel("무역수지\n(백만 USD)")
    ax2.set_ylim(balance.min() * 2.4, balance.max() * 1.3)
    ax2.grid(True, axis="y", linestyle="--", alpha=0.3)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)

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
    save(fig, SAVE)


if __name__ == "__main__":
    yearly = yearly_balance(df, REGIONS)
    periods = period_table(yearly, FOCUS)
    print(yearly)
    print("\n--무역수지 흐름---")
    print(periods)
    plot_trade_diverging()
