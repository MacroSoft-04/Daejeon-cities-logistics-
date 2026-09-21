"""Plot monthly seasonal indices of trade value, weight and unit price for Daejeon vs. all regions.

Seasonal index for month m = (average of month m across years) / (region's overall monthly average) * 100.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.lines import Line2D

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data/processed"
SAVE_DIR = BASE_DIR / "output"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATH = DATA_DIR / "kita_regional_monthly.csv"
SAVE_PATH = SAVE_DIR / "m_Daejeon_region_seasonal_index.jpg"

FOCUS_REGION = "대전"
BENCHMARK_REGION = "전국"
FOCUS_COLOR, BENCHMARK_COLOR = "#c0392b", "#666666"
PEER_COLOR, LABEL_COLOR = "#cfcfcf", "#888888"

FLOWS = {
    "수출": ("수출액_백만불", "수출중량_천톤"),
    "수입": ("수입액_백만불", "수입중량_천톤"),
}
METRICS = ["액", "중량", "단가"]


plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["연월"])
    df["월"] = df["연월"].dt.month

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


def seasonal_indices(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return {panel name: DataFrame(index=month, columns=region)} of seasonal indices."""
    columns = [c for pair in FLOWS.values() for c in pair]
    monthly_mean = df.groupby(["지역명", "월"])[columns].mean()
    overall_mean = df.groupby("지역명")[columns].mean()
    value_index = monthly_mean.div(overall_mean, level="지역명") * 100

    panels = {}
    for flow, (value_col, weight_col) in FLOWS.items():
        panels[f"{flow}액"] = value_index[value_col].unstack(level="지역명")
        panels[f"{flow}중량"] = value_index[weight_col].unstack(level="지역명")
        # Unit price is computed as mean value / mean weight (a weighted price), not as the
        # mean of the monthly unit-price column, so a low-volume month with an odd price
        # cannot dominate. With that definition the price index equals value index /
        # weight index * 100, keeping the three rows internally consistent.
        panels[f"{flow}단가"] = panels[f"{flow}액"] / panels[f"{flow}중량"] * 100
    return panels


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
    )
    ax.plot(months, index_df[FOCUS_REGION], color=FOCUS_COLOR, linewidth=3)

    y_min, y_max = index_df.min().min(), index_df.max().max()
    pad = (y_max - y_min) * 0.08
    ax.set_ylim(y_min - pad, y_max + pad)

    label_y = spread_labels(
        index_df.loc[months.max(), peers],
        min_gap=(y_max - y_min) * 0.055,
        upper=y_max + pad,
    )
    for region, y in label_y.items():
        ax.annotate(
            region,
            xy=(months.max(), y),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=LABEL_COLOR,
            annotation_clip=False,
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlim(months.min() - 0.3, months.max() + 1.0)
    ax.set_xticks(months)
    ax.set_xticklabels([f"{m}월" for m in months])
    ax.grid(linestyle="--", alpha=0.4)
    for spine in ax.spines.values():
        spine.set_color("#cccccc")


def main() -> None:
    df = load_data(DATA_PATH)
    first_year, last_year = df["연도"].min(), df["연도"].max()
    peers = sorted(set(df["지역명"]) - {FOCUS_REGION, BENCHMARK_REGION})
    panels = seasonal_indices(df)

    print(
        f"Years used: {first_year}-{last_year} ({df['연도'].nunique()} complete years)"
    )
    print(f"Peer regions: {', '.join(peers)}")
    for name, frame in panels.items():
        print(f"\n[{name}] seasonal index")
        print(frame[[FOCUS_REGION, BENCHMARK_REGION, *peers]].round(1).to_string())

    fig, axes = plt.subplots(len(METRICS), len(FLOWS), figsize=(16, 17), sharex=True)
    for row, metric in enumerate(METRICS):
        for col, flow in enumerate(FLOWS):
            name = f"{flow}{metric}"
            plot_panel(axes[row, col], panels[name], peers, name)
            axes[row, col].set_ylabel("계절지수 (월평균=100)")

    fig.suptitle(
        f"대전·전국 시도 수출입 규모 및 단가 월별 계절지수 ({first_year}~{last_year} 평균)",
        fontsize=20,
        fontweight="bold",
        y=0.995,
    )
    handles = [
        Line2D([], [], color=FOCUS_COLOR, linewidth=3),
        Line2D([], [], color=BENCHMARK_COLOR, linewidth=2.2, linestyle="--"),
        Line2D([], [], color=PEER_COLOR, linewidth=1.2),
    ]
    fig.legend(
        handles,
        [FOCUS_REGION, BENCHMARK_REGION, "기타 시도"],
        loc="upper center",
        ncol=3,
        frameon=False,
        fontsize=13,
        bbox_to_anchor=(0.5, 0.975),
    )
    fig.text(
        0.99,
        0.002,
        "자료: 한국무역협회(KITA) 지역별 수출입 통계 · 단가 = 월평균 금액 ÷ 월평균 중량",
        ha="right",
        fontsize=9,
        color="gray",
    )

    fig.tight_layout(rect=(0, 0.01, 1, 0.96))
    SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SAVE_PATH, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
