"""
====================================================================
* Author: Minseo Kim
* Data:
    - data/processed/estab_survey_daejeon_long.csv   (전국사업체조사, 전체)
    - data/processed/mining_mfg_by_sido_long.csv     (광업제조업조사, 10인 이상)
* Chart: the two surveys move in opposite directions, which is what
  identifies the decline as concentrated in the smallest establishments.
* Note: the two surveys cover different universes, so the panels are indexed
  separately and the absolute counts are never placed on a shared axis.
* Output: output/11_estab_by_scale.jpg
====================================================================
"""

import pandas as pd
import matplotlib.pyplot as plt

from chart_utils import PALETTE, save, use_korean_font
from kosis_utils import PROJECT_ROOT

ESTAB_SRC = PROJECT_ROOT / "data/processed/estab_survey_daejeon_long.csv"
MFG_SRC = PROJECT_ROOT / "data/processed/mining_mfg_by_sido_long.csv"
REGION = "대전광역시"
INDUSTRY = "제조업"

use_korean_font()

estab = pd.read_csv(ESTAB_SRC)
mfg = pd.read_csv(MFG_SRC)

total = (
    estab[(estab["산업별"] == INDUSTRY) & (estab["지표"] == "사업체수")]
    .set_index("연도")["값"]
    .sort_index()
)
large = (
    mfg[
        (mfg["시도별"] == REGION)
        & (mfg["산업별"] == INDUSTRY)
        & (mfg["지표"] == "사업체수")
    ]
    .set_index("연도")["값"]
    .sort_index()
)

years = sorted(set(total.index) & set(large.index))
total, large = total.loc[years], large.loc[years]
base = years[0]

series = [
    (total, f"전체 사업체\n(전국사업체조사)", PALETTE["accent"]),
    (large, f"10인 이상 사업체\n(광업제조업조사)", PALETTE["primary"]),
]

fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

for ax, (data, label, color) in zip(axes, series):
    indexed = data / data.loc[base] * 100
    ax.plot(years, indexed, marker="o", markersize=7, linewidth=2.8, color=color)
    ax.fill_between(years, 100, indexed, color=color, alpha=0.10)
    ax.axhline(100, color="#c8ced4", linestyle="--", linewidth=1)

    for year in years:
        ax.annotate(
            f"{data.loc[year]:,.0f}",
            xy=(year, indexed.loc[year]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color=PALETTE["text"],
        )

    change = (data.iloc[-1] / data.iloc[0] - 1) * 100
    ax.set_title(f"{label}   {change:+.1f}%", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(years)
    ax.set_xlabel("연도")
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

axes[0].set_ylabel(f"사업체수 지수 ({base}년=100)")

# Headroom for the value labels sitting above each marker.
low, high = axes[0].get_ylim()
axes[0].set_ylim(low, high + (high - low) * 0.10)

fig.suptitle(
    "사라진 것은 영세 사업체였다",
    fontsize=15,
    fontweight="bold",
    y=1.02,
)
fig.text(
    0.5,
    -0.04,
    "두 조사는 대상 범위가 달라 절대 수치를 직접 비교할 수 없으므로 각각 지수화함",
    ha="center",
    fontsize=9,
    color="#7a848d",
)

save(fig, "11_estab_by_scale.jpg")
