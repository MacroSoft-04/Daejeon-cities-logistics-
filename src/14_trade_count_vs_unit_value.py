"""
====================================================================
* Author: Minseo Kim
* Data: data/raw/customs_sido_trade_daejeon.csv (관세청 시도별 수출입실적 API)
* Chart: exports and imports move in opposite directions. Counts and value
  per shipment are split into two panels because the story is the divergence
  between them, not the totals.
* Note: the API publishes counts and USD amounts only, no weight, so shipment
  count stands in for handling volume.
* Output: output/14_trade_count_vs_unit_value.jpg
====================================================================
"""

import matplotlib.pyplot as plt
import pandas as pd

from chart_utils import PALETTE, save, use_korean_font
from kosis_utils import PROJECT_ROOT

SRC = PROJECT_ROOT / "data/raw/customs_sido_trade_daejeon.csv"
# The API reports amounts in thousands of USD.
THOUSAND_USD = 1_000
# The latest year is still being accumulated; its half-size totals would read
# as a collapse rather than an incomplete count.
LATEST_COMPLETE_YEAR = 2025

use_korean_font()

df = pd.read_csv(SRC)
df = df[df["연도"] <= LATEST_COMPLETE_YEAR].sort_values("연도")
years = df["연도"].tolist()
base = years[0]

df["수출_건당"] = df["expUsdAmt"] / df["expCnt"] * THOUSAND_USD
df["수입_건당"] = df["impUsdAmt"] / df["impCnt"] * THOUSAND_USD

panels = [
    {
        "title": "신고 건수",
        "series": {"수출": df["expCnt"], "수입": df["impCnt"]},
        "fmt": "{:,.0f}건",
    },
    {
        "title": "건당 금액",
        "series": {"수출": df["수출_건당"], "수입": df["수입_건당"]},
        "fmt": "{:,.0f}USD",
    },
]
colors = {"수출": PALETTE["primary"], "수입": PALETTE["accent"]}

fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)

for ax, panel in zip(axes, panels):
    for name, values in panel["series"].items():
        indexed = values.to_numpy() / values.iloc[0] * 100
        ax.plot(
            years,
            indexed,
            marker="o",
            markersize=7,
            linewidth=2.8,
            color=colors[name],
            label=name,
        )
        ax.annotate(
            f"{indexed[-1]:.0f}",
            xy=(years[-1], indexed[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontweight="bold",
            color=colors[name],
        )

    ax.axhline(100, color="#c8ced4", linestyle="--", linewidth=1)
    ax.set_title(f"{panel['title']}\n", fontsize=11.5, fontweight="bold", pad=12)
    ax.set_xticks(years)
    ax.set_xlabel("연도")
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    ax.legend(frameon=False, loc="best", fontsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

axes[0].set_ylabel(f"지수 ({base}년=100)")

span_x = years[-1] - years[0]
for ax in axes:
    ax.set_xlim(years[0] - span_x * 0.05, years[-1] + span_x * 0.14)

fig.text(
    0.5,
    -0.04,
    f"자료: 관세청 시도별 수출입실적 (중량 미공표로 건수를 취급량 대리지표로 사용) | "
    f"{LATEST_COMPLETE_YEAR}년까지, 이후는 집계 진행 중",
    ha="center",
    fontsize=9,
    color="#7a848d",
)

save(fig, "14_trade_count_vs_unit_value.jpg")
