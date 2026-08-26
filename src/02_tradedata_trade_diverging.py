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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils_chart import PALETTE, save, use_korean_font
from utils_kosis import PROJECT_ROOT

SRC = PROJECT_ROOT / "data/processed/tradedata_dj_2020_2025.csv"
GROUPS = ["기계 및 전기기기", "수송기기", "화학공업 제품", "기타"]
COLORS = {
    "기계 및 전기기기": PALETTE["primary"],
    "수송기기": PALETTE["accent"],
    "화학공업 제품": "#c8973f",
    "기타": PALETTE["muted"],
}
MILLION = 1_000  # source unit is thousand USD
LABEL_MIN_SHARE = 0.07

use_korean_font()

df = pd.read_csv(SRC)
df["group"] = df["section_name"].where(df["section_name"].isin(GROUPS), "기타")

exports = df.groupby(["year", "group"])["export_usd"].sum().unstack()[GROUPS]
imports = df.groupby(["year", "group"])["import_usd"].sum().unstack()[GROUPS]
balance = df.groupby("year")["balance"].sum() / MILLION

years = exports.index.tolist()
x = np.arange(len(years))
width = 0.6

# The balance line crossed the stacks when drawn on the same axes, so it gets
# its own panel sharing the x axis.
fig, (ax, ax2) = plt.subplots(
    2, 1, figsize=(12, 9), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
)

for frame, sign in ((exports, 1), (imports, -1)):
    totals = frame.sum(axis=1)
    bottom = np.zeros(len(years))
    for group in GROUPS:
        values = frame[group].to_numpy(dtype=float) / MILLION * sign
        ax.bar(
            x,
            values,
            bottom=bottom,
            width=width,
            color=COLORS[group],
            edgecolor="white",
            linewidth=0.8,
            label=group if sign == 1 else None,
        )
        for xi, (value, base) in enumerate(zip(values, bottom)):
            share = frame[group].iloc[xi] / totals.iloc[xi]
            if share < LABEL_MIN_SHARE:
                continue
            ax.text(
                xi,
                base + value / 2,
                f"{share * 100:.0f}%",
                ha="center",
                va="center",
                fontsize=8.5,
                color="#2c3e50" if group == "기타" else "white",
            )
        bottom += values

ax.axhline(0, color="#1c1c1c", linewidth=1.2)
ax.set_ylabel("금액 (백만 USD)")
# Values below the axis are import volumes, not negative amounts.
ax.yaxis.set_major_formatter(lambda value, _: f"{abs(value):,.0f}")
ax.set_title(
    "대전 수출입 구조: 기계를 내보내고 화학을 들여온다",
    fontsize=15,
    fontweight="bold",
    pad=16,
)
ax.grid(True, axis="y", linestyle="--", alpha=0.3)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)

ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False, title="품목 구분")

bar_colors = [PALETTE["positive"] if v >= 0 else PALETTE["negative"] for v in balance]
ax2.bar(x, balance, width=width, color=bar_colors)
for xi, value in enumerate(balance):
    ax2.annotate(
        f"{value:+,.0f}",
        xy=(xi, value),
        xytext=(0, 8 if value >= 0 else -22),
        textcoords="offset points",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color=PALETTE["positive"] if value >= 0 else PALETTE["negative"],
    )
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
ax.text(-0.62, span[1] * 0.9, "수출 ▲", fontsize=11, fontweight="bold", color="#2c3e50")
ax.text(-0.62, span[0] * 0.9, "수입 ▼", fontsize=11, fontweight="bold", color="#2c3e50")

fig.text(
    0.5,
    -0.01,
    f"막대 안 숫자는 각 흐름 내 비중 ({LABEL_MIN_SHARE * 100:.0f}% 미만 생략) | "
    "자료: 관세청 무역통계",
    ha="center",
    fontsize=9,
    color="#7a848d",
)

fig.tight_layout()
save(fig, "02_trade_diverging.jpg")
