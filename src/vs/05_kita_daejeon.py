"""
====================================================================
* Author: Minseo Kim
* Data Source:
    - data/processed/kita_regional_yearly.csv
* Selection criteria:
    - Daejeon and the top 3 regions by trade value in the most recent year
    - National total for reference
* Output: output/05_Daejeon_trade_flow.jpg
====================================================================
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(".")
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
    df["총교역중량_천톤"] = df["수출중량_천톤"] + df["수입중량_천톤"]
    return df


def index_to_base(df, cols):
    """Daejeon is ~1/146 of the national total, so levels can't share an axis."""
    df = df.sort_values("연도")
    for col in cols:
        df[f"{col}_지수"] = df[col] / df[col].iloc[0] * 100
    return df


VALUE_COLS = [
    "총교역액_백만불",
    "총교역중량_천톤",
]

PANELS = [
    ("총교역액_백만불_지수", "총교역액", f"지수 ({y_min}년=100)"),
    ("총교역중량_천톤_지수", "총교역중량", f"지수 ({y_min}년=100)"),
]

base = YEARLY[YEARLY["연도"] <= latest_year].pipe(add_total_trade_columns)

top3_regions = (
    base[
        (base["연도"] == latest_year)
        & (base["지역명"] != "전국")
        & (base["지역명"] != "대전")
    ]
    .nlargest(3, "총교역액_백만불")["지역명"]
    .tolist()
)

print(f"Top 3 regions by trade value in {latest_year}: {top3_regions}")

REGIONS = top3_regions + ["대전", "전국"]

series = {
    region: index_to_base(base[base["지역명"] == region].copy(), VALUE_COLS)
    for region in REGIONS
}
STYLES = {
    "대전": dict(color="#c0392b", linewidth=2.8, zorder=3),
    "전국": dict(color="dimgrey", linewidth=2, linestyle="--", zorder=2),
}

TOP3_COLORS = {
    region: color
    for region, color in zip(top3_regions, ["plum", "lightsalmon", "lightgray"])
}


def get_style(region):
    if region in STYLES:
        return STYLES[region]

    return dict(
        color=TOP3_COLORS.get(region),
        linewidth=1.2,
        zorder=1,
    )


fig, axes = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

for ax, (col, metric, ylabel) in zip(axes, PANELS):
    for region, df in series.items():
        label = "_nolegend_" if region in top3_regions else region
        ax.plot(
            df["연도"],
            df[col],
            label=label,
            **get_style(region),
        )

        if region in top3_regions:
            last = df.iloc[-1]

            ax.text(
                last["연도"] + 0.2,
                last[col],
                region,
                fontsize=9,
                color="gray",
                va="center",
            )

    ax.legend(loc="upper left", fontsize=10, frameon=False)
    ax.set_title(
        f"대전·주요 지역 {metric} 추이 ({y_min}~{y_max})",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.6)

SAVE_PATH = SAVE_DIR / "05_Daejeon_trade_flow.jpg"
plt.savefig(SAVE_PATH, dpi=300, bbox_inches="tight")
plt.close(fig)
