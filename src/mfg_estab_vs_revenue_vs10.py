"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/kosis_estab_survey.csv (전국사업체조사)
* Chart: Daejeon manufacturing indexed to the cleaning step's base year,
  showing establishments falling while revenue rises. National figures are
  quoted in the note so the pattern is not read as Daejeon-specific.
* Output: output/10_mfg_estab_vs_revenue.jpg
====================================================================
"""

import matplotlib.pyplot as plt
import pandas as pd

from chart_utils import PALETTE, save, use_korean_font
from kosis_utils import PROJECT_ROOT

SRC = PROJECT_ROOT / "data/processed/kosis_estab_survey.csv"
REGION = "대 전"
NATIONAL = "전 국"
INDUSTRY = "제조업"
SERIES = {
    "매출액": PALETTE["primary"],
    "종사자수": PALETTE["muted"],
    "사업체수": PALETTE["accent"],
}

use_korean_font()

df = pd.read_csv(SRC)
df = df[df["산업별"] == INDUSTRY]


def pivot(region: str, value_col: str) -> pd.DataFrame:
    return (
        df[df["행정구역별"] == region]
        .pivot(index="연도", columns="지표", values=value_col)
        .sort_index()
    )


indexed = pivot(REGION, "지수")
raw = pivot(REGION, "값")
national = pivot(NATIONAL, "지수")

# The base year is fixed in the cleaning step, so read it back from the data
# rather than assuming it is the first year on the axis.
base_year = indexed.index[(indexed == 100).all(axis=1)][0]

fig, ax = plt.subplots(figsize=(9, 5.5))

for metric, color in SERIES.items():
    ax.plot(
        indexed.index,
        indexed[metric],
        marker="o",
        markersize=6,
        linewidth=2.6,
        color=color,
        label=metric,
    )
    ax.annotate(
        f"{indexed[metric].iloc[-1]:.1f}",
        xy=(indexed.index[-1], indexed[metric].iloc[-1]),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontweight="bold",
        color=color,
    )

ax.axhline(100, color="#c8ced4", linestyle="--", linewidth=1)
ax.set_xticks(indexed.index)
ax.set_xlabel("연도")
ax.set_ylabel(f"지수 ({base_year}년=100)")
ax.set_title(
    f"대전 {INDUSTRY}: 사업체는 줄고 매출은 늘었다",
    fontsize=15,
    fontweight="bold",
    pad=14,
)
ax.grid(True, axis="y", linestyle="--", alpha=0.35)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)

# Headroom on the right so the end-of-line labels are not clipped.
span = indexed.index[-1] - indexed.index[0]
ax.set_xlim(indexed.index[0] - span * 0.04, indexed.index[-1] + span * 0.12)
ax.legend(frameon=False, loc="lower left")

first, last = raw.index[0], raw.index[-1]
note = (
    f"{first}→{last} 대전 사업체수 {raw.loc[last, '사업체수'] - raw.loc[first, '사업체수']:+,.0f}개, "
    f"매출액 {(raw.loc[last, '매출액'] / raw.loc[first, '매출액'] - 1) * 100:+.1f}%   |   "
    f"전국 사업체수 지수 {national.loc[last, '사업체수']:.1f}, 매출액 지수 {national.loc[last, '매출액']:.1f}"
)
fig.text(0.5, -0.02, note, ha="center", fontsize=10, color=PALETTE["text"])
fig.text(
    0.5,
    -0.06,
    "자료: 통계청 전국사업체조사 (사업체 단위, 등록기반)",
    ha="center",
    fontsize=8.5,
    color="#7a848d",
)

save(fig, "10_mfg_estab_vs_revenue.jpg")
