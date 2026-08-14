"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/estab_survey_daejeon_long.csv (전국사업체조사)
* Chart: diverging bars of establishment growth by industry, placing the
  manufacturing decline against the industries that expanded.
* Output: output/12_industry_change.jpg
====================================================================
"""

import pandas as pd
import matplotlib.pyplot as plt

from chart_utils import PALETTE, save, use_korean_font
from kosis_utils import PROJECT_ROOT

SRC = PROJECT_ROOT / "data/processed/estab_survey_daejeon_long.csv"
TOTAL_ROW = "전체 산업"
HIGHLIGHT = {"제조업", "정보통신업", "운수 및 창고업"}
MIN_BASE_COUNT = 100

use_korean_font()

df = pd.read_csv(SRC)
wide = (
    df[df["지표"] == "사업체수"]
    .pivot(index="산업별", columns="연도", values="값")
    .sort_index(axis=1)
)
first, last = wide.columns[0], wide.columns[-1]

# Industries with a tiny base swing wildly in percentage terms and would
# dominate the chart without saying anything about the city's structure.
wide = wide[(wide.index != TOTAL_ROW) & (wide[first] >= MIN_BASE_COUNT)]

change = ((wide[last] / wide[first] - 1) * 100).sort_values()
# Colour carries the sign only. Using it for emphasis as well made a growing
# industry read as a shrinking one, so emphasis moves to opacity.
colors = [PALETTE["positive"] if value > 0 else PALETTE["negative"] for value in change]
alphas = [1.0 if name in HIGHLIGHT else 0.45 for name in change.index]

fig, ax = plt.subplots(figsize=(9, 7))
bars = ax.barh(change.index, change.values, color=colors, alpha=None, height=0.7)
for bar, alpha in zip(bars, alphas):
    bar.set_alpha(alpha)

for label in ax.get_yticklabels():
    if label.get_text() in HIGHLIGHT:
        label.set_fontweight("bold")

for bar, value, alpha in zip(bars, change.values, alphas):
    offset = 0.6 if value >= 0 else -0.6
    ax.text(
        value + offset,
        bar.get_y() + bar.get_height() / 2,
        f"{value:+.1f}%",
        va="center",
        ha="left" if value >= 0 else "right",
        fontsize=9,
        fontweight="bold" if alpha == 1.0 else "normal",
        alpha=alpha,
        color=PALETTE["positive"] if value > 0 else PALETTE["negative"],
    )

ax.axvline(0, color="#7a848d", linewidth=1)
ax.set_xlabel(f"사업체수 증감률 (%, {first}→{last})")
ax.set_title(
    f"제조업이 줄어든 자리에 무엇이 들어섰나",
    fontsize=15,
    fontweight="bold",
    pad=14,
)
ax.grid(True, axis="x", linestyle="--", alpha=0.3)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)

margin = (change.max() - change.min()) * 0.12
ax.set_xlim(change.min() - margin, change.max() + margin)

fig.text(
    0.5,
    0.02,
    f"자료: 통계청 전국사업체조사 | {first}년 사업체수 {MIN_BASE_COUNT}개 미만 산업 제외",
    ha="center",
    fontsize=8.5,
    color="#7a848d",
)

save(fig, "12_industry_change.jpg")
