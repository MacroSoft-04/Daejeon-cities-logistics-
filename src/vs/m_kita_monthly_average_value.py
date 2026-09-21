"""Plot Daejeon's average export and import value by calendar month (KITA regional data)."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data/processed"
SAVE_DIR = BASE_DIR / "output"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATH = DATA_DIR / "kita_regional_monthly.csv"
SAVE_PATH = SAVE_DIR / "m_Daejeon_monthly_avg_value.jpg"

REGION = "대전"
EXPORT_COLOR, IMPORT_COLOR = "#1f77b4", "#d62728"

PANELS = [
    {
        "columns": {"수출액_백만불": "수출액", "수입액_백만불": "수입액"},
        "title": "월별 평균 수출액·수입액",
        "ylabel": "평균 금액 (백만 달러)",
    },
    {
        "columns": {"수출중량_천톤": "수출중량", "수입중량_천톤": "수입중량"},
        "title": "월별 평균 수출중량·수입중량",
        "ylabel": "평균 중량 (천 톤)",
    },
]


def load_complete_years(path: Path, region: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["연월"])
    df = df[df["지역명"] == region].copy()
    df["월"] = df["연월"].dt.month
    # A partial final year would add an extra (and, given the long-run growth trend,
    # higher-than-average) observation only to its early months, biasing those
    # monthly means upward. Keep only years with all 12 months.
    months_per_year = df.groupby("연도")["월"].nunique()
    complete_years = months_per_year[months_per_year == 12].index
    return df[df["연도"].isin(complete_years)]


def plot_monthly_panel(
    ax: plt.Axes, monthly_avg: pd.DataFrame, title: str, ylabel: str
) -> None:
    for column, color in zip(monthly_avg.columns, [EXPORT_COLOR, IMPORT_COLOR]):
        ax.plot(
            monthly_avg.index,
            monthly_avg[column],
            marker="o",
            linewidth=2,
            color=color,
            label=column,
        )
        ax.axhline(
            monthly_avg[column].mean(),
            color=color,
            linestyle=":",
            linewidth=1,
            alpha=0.6,
        )

    ax.set_title(title, fontsize=12, loc="left")
    ax.set_ylabel(ylabel)

    # Pad the y-range from the data instead of starting at 0, so month-to-month
    # differences are visible; the padding keeps markers off the frame.
    y_min, y_max = monthly_avg.min().min(), monthly_avg.max().max()
    pad = (y_max - y_min) * 0.15
    ax.set_ylim(y_min - pad, y_max + pad)

    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(
        title="구분 (점선: 12개월 평균)",
        frameon=False,
        loc="upper left",
        fontsize=9,
        title_fontsize=9,
    )


def main() -> None:
    df = load_complete_years(DATA_PATH, REGION)
    first_year, last_year = df["연도"].min(), df["연도"].max()
    print(
        f"Region: {REGION}, years {first_year}-{last_year} ({df['연도'].nunique()} complete years)"
    )

    fig, axes = plt.subplots(
        len(PANELS), 1, figsize=(10, 4.2 * len(PANELS)), sharex=True
    )
    for ax, panel in zip(axes, PANELS):
        monthly_avg = (
            df.groupby("월")[list(panel["columns"])]
            .mean()
            .rename(columns=panel["columns"])
        )
        print(monthly_avg.round(1).to_string(), end="\n\n")
        plot_monthly_panel(ax, monthly_avg, panel["title"], panel["ylabel"])

    months = sorted(df["월"].unique())
    axes[-1].set_xticks(months)
    axes[-1].set_xticklabels([f"{m}월" for m in months])
    axes[-1].set_xlabel("월")

    fig.suptitle(
        f"{REGION} 월별 평균 수출입 금액·중량 ({first_year}–{last_year})", fontsize=14
    )
    fig.text(
        0.99,
        0.01,
        "자료: 한국무역협회(KITA) 지역별 수출입 통계",
        ha="right",
        fontsize=8,
        color="gray",
    )

    fig.tight_layout()
    fig.savefig(SAVE_PATH, dpi=200, bbox_inches="tight")
    print(f"Saved: {SAVE_PATH}")


if __name__ == "__main__":
    main()
