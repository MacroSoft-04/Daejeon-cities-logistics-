"""
====================================================================
* Author: Minseo Kim
* Data:
    - data/processed/kosis_estab_survey.csv        (전국사업체조사, 전체)
    - data/processed/mining_mfg_by_sido_long.csv   (광업제조업조사, 10인 이상)
  Two separate surveys are required: the contrast between them is the finding.
* Chart: the two surveys move in opposite directions, which identifies the
  decline as concentrated in the smallest establishments. The national line
  separates a nationwide trend from what is specific to Daejeon.
* Note: the surveys cover different universes, so the panels are indexed
  separately and the absolute counts never share an axis.
* Output: output/11_estab_by_scale.jpg
====================================================================
"""

import matplotlib.pyplot as plt
import pandas as pd

from chart_utils import PALETTE, save, use_korean_font
from kosis_utils import PROJECT_ROOT

ESTAB_SRC = PROJECT_ROOT / "data/processed/kosis_estab_survey.csv"
MFG_SRC = PROJECT_ROOT / "data/processed/kosis_mining_mfg.csv"
INDUSTRY = "제조업"
METRIC = "사업체수"

# The two sources spell regions differently, so each keeps its own labels.
ESTAB = {"col": "행정구역별", "local": "대전", "national": "전국"}
MFG = {"col": "시도별", "local": "대전광역시", "national": "전국"}

use_korean_font()


def series(frame: pd.DataFrame, spec: dict, scope: str) -> pd.Series:
    subset = frame[
        (frame[spec["col"]] == spec[scope])
        & (frame["산업별"] == INDUSTRY)
        & (frame["지표"] == METRIC)
    ]
    return subset.set_index("연도")["값"].sort_index()


estab = pd.read_csv(ESTAB_SRC)
mfg = pd.read_csv(MFG_SRC)

panels = [
    {
        "title": "전체 사업체",
        "local": series(estab, ESTAB, "local"),
        "national": series(estab, ESTAB, "national"),
        "color": PALETTE["accent"],
    },
    {
        "title": "10인 이상 사업체",
        "local": series(mfg, MFG, "local"),
        "national": series(mfg, MFG, "national"),
        "color": PALETTE["primary"],
    },
]

years = sorted(set.intersection(*(set(p["local"].index) for p in panels)))
base = years[0]
for panel in panels:
    panel["local"] = panel["local"].loc[years]
    panel["national"] = panel["national"].loc[years]

fig, axes = plt.subplots(1, 2, figsize=(11, 5.4), sharey=True)

for ax, panel in zip(axes, panels):
    local, national, color = panel["local"], panel["national"], panel["color"]
    indexed = local / local.loc[base] * 100

    ax.plot(
        years,
        indexed,
        marker="o",
        markersize=7,
        linewidth=2.8,
        color=color,
        label="대전",
        zorder=3,
    )
    ax.fill_between(years, 100, indexed, color=color, alpha=0.10)
    ax.plot(
        years,
        national / national.loc[base] * 100,
        marker="o",
        markersize=4,
        linewidth=2,
        linestyle="--",
        color=PALETTE["muted"],
        label="전국",
        zorder=2,
    )
    ax.axhline(100, color="#c8ced4", linestyle="--", linewidth=1)

    for year in years:
        ax.annotate(
            f"{local.loc[year]:,.0f}",
            xy=(year, indexed.loc[year]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color=PALETTE["text"],
        )

    local_change = (local.iloc[-1] / local.iloc[0] - 1) * 100
    national_change = (national.iloc[-1] / national.iloc[0] - 1) * 100
    ax.set_title(
        f"{panel['title']}   대전 {local_change:+.1f}%   (전국 {national_change:+.1f}%)",
        fontsize=11.5,
        fontweight="bold",
        pad=12,
    )
    ax.set_xticks(years)
    ax.set_xlabel("연도")
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    ax.legend(frameon=False, loc="best", fontsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

axes[0].set_ylabel(f"{METRIC} 지수 ({base}년=100)")

# Headroom for the value labels sitting above each marker.
low, high = axes[0].get_ylim()
axes[0].set_ylim(low, high + (high - low) * 0.10)

fig.suptitle(
    "대전 제조업 사업체수: 규모별 추이", fontsize=15, fontweight="bold", y=1.02
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
