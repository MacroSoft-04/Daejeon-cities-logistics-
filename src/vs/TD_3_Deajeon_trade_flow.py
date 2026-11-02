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
from core.utils_chart import PALETTE, save, use_korean_font

data_dir = BASE_DIR / "data" / "processed"
FILE_PATH = data_dir / "tradedata_2000_2025_4_added.csv"

EX_GROUPS = [
    "기계 및 전기기기",
    "플라스틱 및 고무 제품",
    "펄프 및 종이 제품",
    "기타",
]

IM_GROUPS = [
    "광물성 생산품",
    "기계 및 전기기기",
    "비금속 및 그 제품",
    "화학공업 제품",
    "기타",
]

COLORS = {
    "기계 및 전기기기": PALETTE["primary"],
    "플라스틱 및 고무 제품": "#3498db",
    "펄프 및 종이 제품": "#fcbc44",
    "화학공업 제품": "#9bd439",
    "광물성 생산품": PALETTE["accent"],
    "비금속 및 그 제품": "#9b59b6",
    "기타": PALETTE["muted"],
}

MILLION = 1_000  # source unit is thousand USD
LABEL_MIN_SHARE = 0.15

use_korean_font()

df = pd.read_csv(FILE_PATH)
df = df[df["지역"] == "대전광역시"].copy()  # Filter for Daejeon
ratio_col = {"수출금액": "수출비율", "수입금액": "수입비율"}


def sections(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Find the top commodity groups by sectional import/export value average."""
    frame = df.copy()
    amount_cols = list(ratio_col.keys())
    ratio_cols = list(ratio_col.values())

    group_totals = frame.groupby(["기간", "부명약칭"])[amount_cols].transform("sum")
    year_totals = frame.groupby("기간")[amount_cols].transform("sum")
    frame[list(ratio_col.values())] = (
        group_totals.div(year_totals).mul(100).rename(columns=ratio_col)
    )
    filtered = frame[frame[ratio_cols].gt(10).any(axis=1)]

    average = filtered.groupby("부명약칭")[ratio_cols].mean()

    ex_rank = (
        average[["수출비율"]].sort_values("수출비율", ascending=False).reset_index()
    )

    im_rank = (
        average[["수입비율"]].sort_values("수입비율", ascending=False).reset_index()
    )
    return ex_rank, im_rank


balance = df.groupby("기간")["무역수지"].sum() / MILLION


def balance_table() -> pd.DataFrame:
    """Return the trade balance in million USD."""
    balance_table = pd.DataFrame(
        {
            "연도": balance.index,
            "무역수지": balance.values,
        }
    )
    print(f"\n무역수지 (백만 USD):")
    return print(balance_table.to_string(index=False))


def sections_check():
    ex_rank, im_rank = sections(df)
    print("Export Rank:")
    print(ex_rank.to_string(index=False))
    print("\nImport Rank:")
    print(im_rank.to_string(index=False))


def plot_trade_diverging():
    """Plot exports above the axis, imports below, stacked by commodity group,
    with the trade balance drawn on the same scale.
    """
    df["ex_group"] = df["부명약칭"].where(df["부명약칭"].isin(EX_GROUPS), "기타")
    df["im_group"] = df["부명약칭"].where(df["부명약칭"].isin(IM_GROUPS), "기타")

    exports = df.groupby(["기간", "ex_group"])["수출금액"].sum().unstack()[EX_GROUPS]
    imports = df.groupby(["기간", "im_group"])["수입금액"].sum().unstack()[IM_GROUPS]
    balance = df.groupby("기간")["무역수지"].sum() / MILLION

    years = exports.index.tolist()
    x = np.arange(len(years))
    width = 0.6

    # The balance line crossed the stacks when drawn on the same axes, so it gets
    # its own panel sharing the x axis.
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(12, 9), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )

    groups = EX_GROUPS + IM_GROUPS
    seen_labels = set()

    for frame, groups, sign in ((exports, EX_GROUPS, 1), (imports, IM_GROUPS, -1)):
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
    save(fig, "TD_2_Daejeon_trade_diverging.jpg")


sections_check()
plot_trade_diverging()
