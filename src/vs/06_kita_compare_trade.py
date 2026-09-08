"""
====================================================================
* Author: Minseo Kim
* Purpose:      Compare Daejeon's trade trends with major benchmark regions.
* Input:        data/processed/kita_regional_yearly.csv
* Output:       output/05_Daejeon_trade_flow.jpg
* Scope:        Uses complete annual data through the latest complete year;
*               compares Daejeon with the top 3 regions by latest-year
*               total trade value, plus the national total as reference.
* Notes:        Trade value and weight are indexed to the first year = 100;
*               balance metrics are kept in their original signed form.
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
    df["총교역중량_천톤"] = df["수출중량_천톤"] + df["수입중량_천톤"]
    return df


def add_balance_ratio_columns(df):
    """Daejeon's balance is ~1/90 of the national one in absolute terms, so the
    levels flatten it against the reference lines. Scaling by total trade keeps
    the surplus/deficit sign while making regions comparable."""
    df["수지율_금액"] = df["수지_금액"] / df["총교역액_백만불"] * 100
    df["수지율_중량"] = df["수지_중량"] / df["총교역중량_천톤"] * 100
    return df


def index_to_base(df, cols, base_year):
    """Daejeon is ~1/146 of the national total, so levels can't share an axis."""
    df = df.sort_values("연도")
    base_row = df.loc[df["연도"] == base_year]
    for col in cols:
        df[f"{col}_지수"] = df[col] / base_row[col].iloc[0] * 100
    return df


INDEX_COLS = ["총교역액_백만불", "총교역중량_천톤"]

base = (
    YEARLY[YEARLY["연도"] <= latest_year]
    .pipe(add_total_trade_columns)
    .pipe(add_balance_ratio_columns)
)

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
    ("총교역액_백만불_지수", "총교역액", f"지수 ({y_min}년=100)"),
    ("총교역중량_천톤_지수", "총교역중량", f"지수 ({y_min}년=100)"),
    ("수지율_금액", "교역금액 수지율", "수지 / 총교역액 (%)"),
    ("수지율_중량", "교역중량 수지율", "수지 / 총교역중량 (%)"),
]

STYLES = {
    "대전": dict(color="#c0392b", linewidth=2.8, zorder=3),
    "전국": dict(color="dimgrey", linewidth=2, linestyle="--", zorder=2),
}

TOP3_COLORS = {
    region: color
    for region, color in zip(benchmark_regions, ["plum", "lightsalmon", "lightgray"])
}


def get_style(region):
    if region in STYLES:
        return STYLES[region]

    return dict(
        color=TOP3_COLORS.get(region),
        linewidth=1.2,
        zorder=1,
    )


fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)

for ax, (col, metric, ylabel) in zip(axes.flat, PANELS):
    for region, df in series.items():
        label = "_nolegend_" if region in benchmark_regions else region
        ax.plot(
            df["연도"],
            df[col],
            label=label,
            **get_style(region),
        )

        if region in benchmark_regions:
            last = df.iloc[-1]

            ax.text(
                last["연도"] + 0.2,
                last[col],
                region,
                fontsize=9,
                color="gray",
                va="center",
            )
        if "수지" in col:
            ax.axhline(0, color="black", linewidth=0.8, alpha=0.6)

        ax.legend(loc="upper left", fontsize=10, frameon=False)
        ax.set_title(
            f"대전·주요 지역 {metric} 추이 ({y_min}~{y_max})",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.6)

# Leave room on the right for the inline region labels.
axes.flat[0].set_xlim(y_min - 0.5, y_max + 2.5)

fig.tight_layout()
SAVE_PATH = SAVE_DIR / "05_Daejeon_trade_flow.jpg"
fig.savefig(SAVE_PATH, dpi=300, bbox_inches="tight")
plt.close(fig)
