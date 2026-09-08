"""
====================================================================
* Author: Minseo Kim
* Purpose:      Contrast Daejeon's export and import sides year by year.
* Input:        data/processed/kita_regional_yearly.csv
* Output:       output/06_Daejeon_trade_butterfly.jpg
* Scope:        Single region, complete annual data through the latest
*               complete year.
* Notes:        Export bars rise above the zero line, import bars drop
*               below it; both are plotted from the same absolute values,
*               so axis tick labels are re-signed to positive for reading.
====================================================================
"""

from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Malgun Gothic",
    "AppleGothic",
    "NanumGothic",
    "Noto Sans CJK KR",
]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data/processed"
SAVE_DIR = BASE_DIR / "output"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
YEARLY_PATH = DATA_DIR / "kita_regional_yearly.csv"
YEARLY = pd.read_csv(YEARLY_PATH)

REGION = "대전"
EXPORT_COLOR = "#c0392b"
IMPORT_COLOR = "#2c6fa8"

# The newest year in the source is year-to-date, so its levels are not
# comparable with full years. The clock guard keeps a later refresh from
# discarding a year that has since become complete.
latest_year = min(YEARLY["연도"].max(), date.today().year - 1)

region_df = (
    YEARLY[(YEARLY["지역명"] == REGION) & (YEARLY["연도"] <= latest_year)]
    .sort_values("연도")
    .reset_index(drop=True)
)
y_min, y_max = region_df["연도"].min(), region_df["연도"].max()

# 백만 USD / 천 톤 reduces to USD/kg, so no scaling factor is needed here.
PANELS = [
    ("수출액_백만불", "수입액_백만불", "교역액", "백만 USD"),
    ("수출중량_천톤", "수입중량_천톤", "교역중량", "천 톤"),
]

fig, axes = plt.subplots(len(PANELS), 1, figsize=(14, 12), sharex=True)

for ax, (export_col, import_col, metric, unit) in zip(axes.flat, PANELS):
    ax.bar(
        region_df["연도"],
        region_df[export_col],
        color=EXPORT_COLOR,
        width=0.7,
        label="수출",
    )
    ax.bar(
        region_df["연도"],
        -region_df[import_col],
        color=IMPORT_COLOR,
        width=0.7,
        label="수입",
    )

    ax.axhline(0, color="black", linewidth=0.8)
    # Mirroring is a layout device, not a negative quantity.
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{abs(y):,.0f}"))

    # A shared span keeps the two wings visually comparable within a panel.
    span = max(region_df[export_col].max(), region_df[import_col].max()) * 1.08
    ax.set_ylim(-span, span)

    ax.set_title(f"{metric} ({unit})", fontsize=13, fontweight="bold")
    ax.set_ylabel(unit)
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)
    ax.grid(False, axis="x")

axes.flat[-1].set_xticks(region_df["연도"])
axes.flat[-1].tick_params(axis="x", labelrotation=45)
axes.flat[-1].set_xlabel("연도")

fig.suptitle(
    f"{REGION} 수출·수입 교역액·교역중량 ({y_min}~{y_max})",
    fontsize=16,
    fontweight="bold",
)
# A figure-level legend can't collide with the bars, whichever region is set.
handles, labels = axes.flat[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.955),
    ncol=2,
    fontsize=11,
    frameon=False,
)
fig.tight_layout(rect=(0, 0, 1, 0.94))

SAVE_PATH = SAVE_DIR / "04_Daejeon_trade_above_below.jpg"
fig.savefig(SAVE_PATH, dpi=300, bbox_inches="tight")
plt.close(fig)
