"""
====================================================================
* Author: Minseo Kim
* Purpose:      Compare Daejeon's trade trends with major benchmark regions.
* Input:        data/processed/kita_regional_yearly.csv
* Output:       output/06_Daejeon_trade_flow.jpg
* Scope:        Uses complete annual data through the latest complete year;
*               compares Daejeon with the top 3 regions by latest-year
*               total trade value, plus the national total as reference.
* Notes:        Export and import legs are indexed to the base year = 100;
*               balance metrics are expressed as a share of total trade.
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

latest_year = YEARLY["연도"].max() - 1
daejeon = YEARLY[(YEARLY["지역명"] == "대전") & (YEARLY["연도"] <= latest_year)].copy()
national = YEARLY[(YEARLY["지역명"] == "전국") & (YEARLY["연도"] <= latest_year)].copy()
y_min, y_max = daejeon["연도"].min(), daejeon["연도"].max()


def add_total_trade_columns(df):
    df["총교역액_백만불"] = df["수출액_백만불"] + df["수입액_백만불"]
    return df


def index_to_base(df, cols, base_year):
    """Daejeon is ~1/146 of the national total, so levels can't share an axis."""
    df = df.sort_values("연도")
    base_row = df.loc[df["연도"] == base_year]
    for col in cols:
        df[f"{col}_지수"] = df[col] / base_row[col].iloc[0] * 100
    return df


INDEX_COLS = [
    "수출액_백만불",
    "수입액_백만불",
    "수출중량_천톤",
    "수입중량_천톤",
]

base = YEARLY[YEARLY["연도"] <= latest_year].pipe(add_total_trade_columns)

benchmark_regions = (
    base[
        (base["연도"] == latest_year)
        & (base["지역명"] != "전국")
        & (base["지역명"] != "대전")
    ]
    .nlargest(3, "총교역액_백만불")["지역명"]
    .tolist()
)

print(f"Top 3 regions by trade value in {latest_year}: {benchmark_regions}")

REGIONS = benchmark_regions + ["대전", "전국"]
frames = {region: base[base["지역명"] == region].copy() for region in REGIONS}

# Sejong only enters the series in 2012, so the index base has to be the first
# year every selected region is present in, not each region's own first row.
y_min = max(df["연도"].min() for df in frames.values())
y_max = latest_year

series = {
    region: index_to_base(df[df["연도"] >= y_min], INDEX_COLS, y_min)
    for region, df in frames.items()
}

PANELS = [
    ("수출액_백만불_지수", "수출액", f"지수 ({y_min}년=100)"),
    ("수입액_백만불_지수", "수입액", f"지수 ({y_min}년=100)"),
    ("수출중량_천톤_지수", "수출중량", f"지수 ({y_min}년=100)"),
    ("수입중량_천톤_지수", "수입중량", f"지수 ({y_min}년=100)"),
    ("수출단가_USD_kg", "수출단가", "단가 (USD/kg)"),
    ("수입단가_USD_kg", "수입단가", "단가 (USD/kg)"),
]

STYLES = {
    "대전": dict(color="#c0392b", linewidth=2.8, zorder=3),
    "전국": dict(color="dimgrey", linewidth=2, linestyle="--", zorder=2),
}

TOP3_COLORS = {
    region: color
    for region, color in zip(benchmark_regions, ["plum", "lightsalmon", "lightgray"])
}


def stack_label_positions(values, y_span):
    """Endpoints of the benchmark lines often land within a few points of each
    other, so the raw values would overprint. Push them apart just enough."""
    min_gap = y_span * 0.05
    placed = {}
    for region, value in sorted(values.items(), key=lambda item: item[1]):
        if placed:
            value = max(value, max(placed.values()) + min_gap)
        placed[region] = value
    return placed


def get_style(region):
    if region in STYLES:
        return STYLES[region]

    return dict(
        color=TOP3_COLORS.get(region),
        linewidth=1.2,
        zorder=1,
    )


fig, axes = plt.subplots(3, 2, figsize=(14, 15), sharex=True)

for ax, (col, metric, ylabel) in zip(axes.flat, PANELS):
    for region, df in series.items():
        label = "_nolegend_" if region in benchmark_regions else region
        ax.plot(
            df["연도"],
            df[col],
            label=label,
            **get_style(region),
        )

    endpoints = {region: series[region][col].iloc[-1] for region in benchmark_regions}
    y_lo, y_hi = ax.get_ylim()
    for region, y in stack_label_positions(endpoints, y_hi - y_lo).items():
        ax.text(y_max + 0.3, y, region, fontsize=9, color="gray", va="center")

    ax.set_title(metric, fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.6)


# Leave room on the right for the inline region labels.
axes.flat[0].set_xlim(y_min - 0.5, y_max + 2.5)

fig.suptitle(
    f"대전·주요 지역 수출입 규모 및 단가 추이 ({y_min}~{y_max})",
    fontsize=16,
    fontweight="bold",
)
# One shared legend: every panel draws the same two labelled lines.
handles, labels = axes.flat[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.962),
    ncol=2,
    fontsize=11,
    frameon=False,
)
fig.tight_layout(rect=(0, 0, 1, 0.955))

SAVE_PATH = SAVE_DIR / "06_Daejeon_target_region_trade_flow_volume_weight_unit.jpg"
fig.savefig(SAVE_PATH, dpi=300, bbox_inches="tight")
plt.close(fig)
