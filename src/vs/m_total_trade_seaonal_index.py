"""Plot monthly seasonal indices of total trade value and weight for Daejeon vs. all regions.

Total trade = exports + imports.
Seasonal index for month m = (average of month m across years) / (region's overall monthly average) * 100.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

DATA_PATH = Path("/mnt/user-data/uploads/kita_regional_monthly.csv")
OUTPUT_PATH = Path("/mnt/user-data/outputs/daejeon_total_trade_seasonal_index.png")

FOCUS_REGION = "대전"
BENCHMARK_REGION = "전국"
FOCUS_COLOR, BENCHMARK_COLOR = "#c0392b", "#666666"
PEER_COLOR, LABEL_COLOR = "#cfcfcf", "#888888"

# Panel name -> (export column, import column)
TOTALS = {
    "총교역액": ("수출액_백만불", "수입액_백만불"),
    "총교역중량": ("수출중량_천톤", "수입중량_천톤"),
}


def set_korean_font() -> None:
    available = {f.name for f in font_manager.fontManager.ttflist}
    # Noto CJK ships as a .ttc collection that matplotlib often registers only under
    # its JP face name; that face still contains the full Hangul glyph set.
    candidates = [
        "Malgun Gothic",
        "AppleGothic",
        "NanumGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
        "Noto Sans CJK JP",
    ]
    font = next((name for name in candidates if name in available), None)
    if font is None:
        print("Warning: no Korean font found; Hangul labels may not render.")
    else:
        plt.rcParams["font.family"] = font
    plt.rcParams["axes.unicode_minus"] = False


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["연월"])
    df["월"] = df["연월"].dt.month
    for name, (export_col, import_col) in TOTALS.items():
        df[name] = df[export_col] + df[import_col]

    # Regions whose series starts later (e.g. 세종, created in 2012) are dropped rather
    # than cutting every region down to their shorter window.
    first_year = df["연도"].min()
    region_start = df.groupby("지역명")["연도"].min()
    late_regions = region_start[region_start > first_year].index.tolist()
    if late_regions:
        print(f"Excluded (series starts after {first_year}): {', '.join(late_regions)}")
    df = df[~df["지역명"].isin(late_regions)]

    # Keep only years with all 12 months for every region: a partial year would add an
    # extra, trend-inflated observation to its early months only.
    counts = df.groupby(["연도", "지역명"])["월"].nunique().unstack()
    complete_years = counts[(counts == 12).all(axis=1)].index
    return df[df["연도"].isin(complete_years)]


def seasonal_index(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return DataFrame(index=month, columns=region) of seasonal indices for one column."""
    monthly_mean = df.groupby(["월", "지역명"])[column].mean().unstack()
    overall_mean = df.groupby("지역명")[column].mean()
    return monthly_mean / overall_mean * 100


def spread_labels(y_values: pd.Series, min_gap: float, upper: float) -> pd.Series:
    """Nudge end-of-line label positions apart so they do not overlap."""
    ordered = y_values.sort_values()
    positions = ordered.to_list()
    for i in range(1, len(positions)):
        positions[i] = max(positions[i], positions[i - 1] + min_gap)
    # Pushing labels upward can run the stack off the top of the axes; shift it back down.
    overshoot = max(0.0, positions[-1] - upper)
    return pd.Series([p - overshoot for p in positions], index=ordered.index)


def plot_panel(
    ax: plt.Axes, index_df: pd.DataFrame, peers: list[str], title: str
) -> None:
    months = index_df.index
    ax.axhline(100, color="black", linewidth=0.8, alpha=0.4)

    for region in peers:
        ax.plot(months, index_df[region], color=PEER_COLOR, linewidth=1.2)
    ax.plot(
        months,
        index_df[BENCHMARK_REGION],
        color=BENCHMARK_COLOR,
        linewidth=2.2,
        linestyle="--",
        label=BENCHMARK_REGION,
    )
    ax.plot(
        months,
        index_df[FOCUS_REGION],
        color=FOCUS_COLOR,
        linewidth=3,
        label=FOCUS_REGION,
    )

    y_min, y_max = index_df.min().min(), index_df.max().max()
    pad = (y_max - y_min) * 0.08
    ax.set_ylim(y_min - pad, y_max + pad)

    label_y = spread_labels(
        index_df.loc[months.max(), peers],
        min_gap=(y_max - y_min) * 0.045,
        upper=y_max + pad,
    )
    for region, y in label_y.items():
        ax.annotate(
            region,
            xy=(months.max(), y),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=LABEL_COLOR,
            annotation_clip=False,
        )

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left", frameon=False, fontsize=12)
    ax.set_title(title, fontsize=15, fontweight="bold")
    ax.set_ylabel("계절지수 (월평균=100)")
    ax.set_xlim(months.min() - 0.3, months.max() + 0.8)
    ax.set_xticks(months)
    ax.set_xticklabels([f"{m}월" for m in months])
    ax.grid(linestyle="--", alpha=0.4)
    for spine in ax.spines.values():
        spine.set_color("#cccccc")


def main() -> None:
    set_korean_font()
    df = load_data(DATA_PATH)
    first_year, last_year = df["연도"].min(), df["연도"].max()
    peers = sorted(set(df["지역명"]) - {FOCUS_REGION, BENCHMARK_REGION})
    print(
        f"Years used: {first_year}-{last_year} ({df['연도'].nunique()} complete years)"
    )

    fig, axes = plt.subplots(len(TOTALS), 1, figsize=(15, 11), sharex=True)
    for ax, name in zip(axes, TOTALS):
        index_df = seasonal_index(df, name)
        print(f"\n[{name}] seasonal index")
        print(index_df[[FOCUS_REGION, BENCHMARK_REGION, *peers]].round(1).to_string())
        plot_panel(
            ax,
            index_df,
            peers,
            f"대전·전국 시도 {name} 월별 계절지수 ({first_year}~{last_year} 평균)",
        )

    fig.text(
        0.99,
        0.002,
        "자료: 한국무역협회(KITA) 지역별 수출입 통계 · 총교역 = 수출 + 수입",
        ha="right",
        fontsize=9,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.01, 1, 1))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
