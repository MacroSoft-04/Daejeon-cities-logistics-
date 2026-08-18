"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/kosis_estab_survey.csv (전국사업체조사)
* Chart: how Daejeon's industry mix departs from the national one. Intended
  as the opening exhibit, since the later panels on manufacturing only read
  correctly once it is clear that manufacturing is not the city's core.
* Method: the gap is averaged over every available year rather than read off
  the latest one, so a single year's swing cannot set the ranking. See
  `python src/validation.py gap_stability` for the year-to-year spread.
* Output: output/09_industry_mix_vs_national.jpg
====================================================================
"""

import matplotlib.pyplot as plt
import pandas as pd

from chart_utils import PALETTE, save, use_korean_font
from kosis_utils import PROJECT_ROOT

SRC = PROJECT_ROOT / "data/processed/kosis_estab_survey.csv"
REGION = "대전"
NATIONAL = "전국"
METRIC = "매출액"
TOTAL_ROW = "전체 산업"
MIN_GAP = 1.0  # percentage points; below this the difference is not the story

use_korean_font()

df = pd.read_csv(SRC)
years = sorted(int(y) for y in df["연도"].unique())

revenue = df[df["지표"] == METRIC].pivot_table(
    index=["산업별", "연도"], columns="행정구역별", values="값"
)[[REGION, NATIONAL]]

totals = revenue.xs(TOTAL_ROW, level="산업별")
share = revenue.drop(index=TOTAL_ROW, level="산업별").div(totals, level="연도") * 100

# Average across years first, then rank. Ranking on one year would let a single
# swing decide which industries appear.
gap = (share[REGION] - share[NATIONAL]).groupby("산업별").mean()

# The chart is about divergence, not size, so industries that sit close to the
# national mix are dropped however large they are.
gap = gap[gap.abs() >= MIN_GAP].sort_values()

colors = [PALETTE["primary"] if value > 0 else PALETTE["accent"] for value in gap]

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(gap.index, gap.values, color=colors, height=0.7)

for bar, industry in zip(bars, gap.index):
    value = gap[industry]
    ax.text(
        value + (0.35 if value >= 0 else -0.35),
        bar.get_y() + bar.get_height() / 2,
        f"{value:+.1f}%p",
        va="center",
        ha="left" if value >= 0 else "right",
        fontsize=9,
        color=bar.get_facecolor(),
        fontweight="bold" if abs(value) >= 2 else "normal",
    )

ax.axvline(0, color="#7a848d", linewidth=1)
ax.set_xlabel(f"전국 대비 매출액 비중 차이 (%p, {years[0]}~{years[-1]} 평균)")
ax.set_title(
    "대전은 제조 도시가 아니다",
    fontsize=15,
    fontweight="bold",
    pad=14,
)
ax.grid(True, axis="x", linestyle="--", alpha=0.3)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)

span = gap.max() - gap.min()
ax.set_xlim(gap.min() - span * 0.12, gap.max() + span * 0.12)

fig.text(
    0.5,
    0.015,
    f"오른쪽은 전국보다 두꺼운 산업, 왼쪽은 얇은 산업 | {years[0]}~{years[-1]}년 매출액 비중 평균, "
    f"격차 {MIN_GAP:.0f}%p 미만 산업 제외 | 자료: 통계청 전국사업체조사",
    ha="center",
    fontsize=8.5,
    color="#7a848d",
)

fig.tight_layout(rect=(0, 0.035, 1, 1))
save(fig, "09_industry_mix_vs_national.jpg")
