"""
====================================================================
* Author: Minseo Kim
* Purpose:      Compare Daejeon's trade trends with every other region.
* Input:        data/processed/kita_regional_yearly.csv
* Output:       output/05_Daejeon_trade_flow.jpg
* Scope:        Uses complete annual data through the latest complete year;
*               plots all regions that cover the full period, with Daejeon
*               highlighted and the national total as reference.
* Notes:        Trade value and weight are indexed to the first shared year = 100.
====================================================================
"""

import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data/processed"
SAVE_DIR = BASE_DIR / "output"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
YEARLY_PATH = DATA_DIR / "kita_regional_yearly.csv"
YEARLY = pd.read_csv(YEARLY_PATH)

HIGHLIGHT = "대전"
REFERENCE = "전국"
INDEX_COLS = ["총교역액_백만불", "총교역중량_천톤"]


def add_total_trade_columns(df):
    df["총교역액_백만불"] = df["수출액_백만불"] + df["수입액_백만불"]
    df["총교역중량_천톤"] = df["수출중량_천톤"] + df["수입중량_천톤"]
    return df


def index_to_base(df, cols, base_year):
    """Daejeon is ~1/146 of the national total, so levels can't share an axis."""
    df = df.sort_values("연도")
    base_row = df.loc[df["연도"] == base_year]
    for col in cols:
        df[f"{col}_지수"] = df[col] / base_row[col].iloc[0] * 100
    return df


def spread_labels(values, min_gap):
    """End-of-line labels collide once every region is drawn, so nudge them apart
    in ascending order and keep the original vertical ranking."""
    adjusted = {}
    previous = None
    for region, y in sorted(values.items(), key=lambda item: item[1]):
        if previous is not None and y - previous < min_gap:
            y = previous + min_gap
        adjusted[region] = y
        previous = y
    return adjusted


# The most recent year in the file is still accumulating, so it is not comparable.
latest_year = YEARLY["연도"].max() - 1
base = YEARLY[YEARLY["연도"] <= latest_year].pipe(add_total_trade_columns)

y_min = base["연도"].min()
y_max = latest_year

# Every line needs the same index base, so regions that start later (Sejong
# only enters the series in 2012) are reported and left out instead of being
# silently rebased to a different year.
first_year = base.groupby("지역명")["연도"].min()
regions = sorted(first_year.index[first_year <= y_min])
dropped = sorted(set(first_year.index) - set(regions))
if dropped:
    print(f"Excluded (no data in base year {y_min}): {dropped}")

series = {
    region: index_to_base(base[base["지역명"] == region], INDEX_COLS, y_min)
    for region in regions
}
background = [r for r in regions if r not in (HIGHLIGHT, REFERENCE)]

PANELS = [
    ("총교역액_백만불_지수", "총교역액", f"지수 ({y_min}년=100)"),
    ("총교역중량_천톤_지수", "총교역중량", f"지수 ({y_min}년=100)"),
]

STYLES = {
    HIGHLIGHT: dict(color="#c0392b", linewidth=2.8, zorder=3),
    REFERENCE: dict(color="dimgrey", linewidth=2, linestyle="--", zorder=2),
}
BACKGROUND_STYLE = dict(color="lightgray", linewidth=1.0, zorder=1)

fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

for ax, (col, metric, ylabel) in zip(axes.flat, PANELS):
    for region in background:
        ax.plot(
            series[region]["연도"],
            series[region][col],
            label="_nolegend_",
            **BACKGROUND_STYLE,
        )

    for region in (HIGHLIGHT, REFERENCE):
        ax.plot(
            series[region]["연도"],
            series[region][col],
            label=region,
            **STYLES[region],
        )

    ax.legend(loc="upper left", fontsize=10, frameon=False)
    ax.set_title(
        f"대전·전국 시도 {metric} 추이 ({y_min}~{y_max})",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.6)

    last_values = {r: series[r][col].iloc[-1] for r in background}
    bottom, top = ax.get_ylim()
    labels = spread_labels(last_values, (top - bottom) * 0.032)

    for region, y in labels.items():
        ax.text(y_max + 0.3, y, region, fontsize=8, color="gray", va="center")

    # Stacking the labels can push the topmost one past the current limit.
    if max(labels.values()) > top:
        ax.set_ylim(top=max(labels.values()) + (top - bottom) * 0.02)

# Leave room on the right for the inline region labels.
axes.flat[0].set_xlim(y_min - 0.5, y_max + 2.5)

fig.tight_layout()
SAVE_PATH = SAVE_DIR / "05_Daejeon_trade_flow.jpg"
fig.savefig(SAVE_PATH, dpi=300, bbox_inches="tight")
plt.close(fig)
