"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/kosis_estab_survey.csv (전국사업체조사)
* Chart: top revenue industries in Daejeon. The upper panel ranks them by
  the latest year so the selection is set by the data, not by the argument;
  emphasis is applied afterwards. The lower panel tracks the two industries
  the analysis follows, including transport, which sits outside the top five.
* Output: output/13_top_industry_revenue.jpg
====================================================================
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chart_utils import PALETTE, save, use_korean_font
from kosis_utils import PROJECT_ROOT

SRC = PROJECT_ROOT / "data/processed/kosis_estab_survey.csv"
REGION = "대전"
METRIC = "매출액"
TOTAL_ROW = "전체 산업"
TOP_N = 5
FOCUS = ["제조업", "운수 및 창고업"]
TRILLION = 1_000_000  # source unit is 백만원

COLORS = [PALETTE["primary"], PALETTE["accent"], "#2b7a5c", "#c8973f", PALETTE["muted"]]
FOCUS_COLORS = {"제조업": PALETTE["accent"], "운수 및 창고업": "#2b7a5c"}

use_korean_font()

df = pd.read_csv(SRC)
wide = (
    df[(df["행정구역별"] == REGION) & (df["지표"] == METRIC)]
    .pivot(index="산업별", columns="연도", values="값")
    .sort_index(axis=1)
)
years = list(wide.columns)
total = wide.loc[TOTAL_ROW]

# Rank once on the latest year. Re-ranking per year would let industries drop
# in and out of the chart, leaving gaps that read as missing data.
ranked = wide.drop(index=TOTAL_ROW).sort_values(years[-1], ascending=False)
top = ranked.head(TOP_N)
# Transport sits outside the top five by revenue, so it is tracked in the
# lower panel rather than forced into a ranking it does not belong to.
share = wide.loc[FOCUS].div(total, axis=1) * 100
# Manufacturing sits near 16% and transport near 3%, so a shared percentage
# axis flattens the smaller series. Indexing the share shows which way each
# weight moved rather than how large it is.
share_index = share.div(share[years[0]], axis=0) * 100

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(11, 9), gridspec_kw={"height_ratios": [1.35, 1]}
)

x = np.arange(len(years))
width = 0.8 / TOP_N

for i, (industry, row) in enumerate(top.iterrows()):
    offset = (i - (TOP_N - 1) / 2) * width
    growth = (row.iloc[-1] / row.iloc[0] - 1) * 100
    ax1.bar(
        x + offset,
        row.values / TRILLION,
        width=width * 0.92,
        color=COLORS[i],
        alpha=1.0 if industry in FOCUS else 0.45,
        label=f"{industry}  ({growth:+.1f}%)",
    )

ax1.set_xticks(x)
ax1.set_xticklabels(years)
ax1.set_ylabel("매출액 (조 원)")
ax1.set_title(
    f"대전 매출액 상위 {TOP_N}개 산업 ({years[-1]}년 기준)",
    fontsize=15,
    fontweight="bold",
    pad=14,
)
ax1.grid(True, axis="y", linestyle="--", alpha=0.3)
ax1.legend(
    bbox_to_anchor=(1.01, 1),
    loc="upper left",
    frameon=False,
    title=f"{years[-1]}년 매출액 순  ({years[0]}→{years[-1]} 증감률)",
    title_fontsize=9,
    fontsize=9,
)
for side in ("top", "right"):
    ax1.spines[side].set_visible(False)

last_values = share_index.iloc[:, -1].sort_values()
# Nearly equal end values would print the labels on top of each other, so
# neighbours closer than this share of the axis range get nudged apart.
min_gap = (share_index.to_numpy().max() - share_index.to_numpy().min()) * 0.06
nudges, previous = {}, None
for industry, value in last_values.items():
    shift = 0 if previous is None or value - previous >= min_gap else 9
    nudges[industry] = shift
    previous = value

for industry, row in share_index.iterrows():
    color = FOCUS_COLORS[industry]
    growth = (wide.loc[industry].iloc[-1] / wide.loc[industry].iloc[0] - 1) * 100
    ax2.plot(
        years,
        row.values,
        marker="o",
        markersize=7,
        linewidth=2.8,
        color=color,
        label=f"{industry}  ({growth:+.1f}%)",
    )
    ax2.annotate(
        f"{row.iloc[-1]:.1f}",
        xy=(years[-1], row.iloc[-1]),
        xytext=(8, nudges[industry]),
        textcoords="offset points",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=color,
    )

ax2.legend(frameon=False, loc="center left", fontsize=9)

ax2.set_xticks(years)
ax2.set_xlabel("연도")
ax2.axhline(100, color="#c8ced4", linestyle="--", linewidth=1)
ax2.set_ylabel(f"매출 비중 지수 ({years[0]}년=100)")
ax2.grid(True, linestyle="--", alpha=0.35)
for side in ("top", "right"):
    ax2.spines[side].set_visible(False)

span = years[-1] - years[0]
ax2.set_xlim(years[0] - span * 0.04, years[-1] + span * 0.14)

city_growth = (total.iloc[-1] / total.iloc[0] - 1) * 100
fig.text(
    0.5,
    0.02,
    f"대전 전체 산업 매출액은 같은 기간 {city_growth:+.1f}% | "
    f"하단은 전체 대비 비중을 {years[0]}년 기준으로 지수화 (100 초과 = 비중 확대) | "
    "자료: 통계청 전국사업체조사",
    ha="center",
    fontsize=9,
    color="#7a848d",
)

fig.tight_layout(rect=(0, 0.04, 1, 1))
save(fig, "13_top_industry_revenue.jpg")
