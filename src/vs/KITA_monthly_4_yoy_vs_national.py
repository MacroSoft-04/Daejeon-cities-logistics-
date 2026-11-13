"""
====================================================================
* Data: data/processed/kita_regional_monthly_4_added.csv (K-stat)
* Question: does Daejeon's trade follow the national trend less than
  comparable regions do? This tests the premise behind choosing Daejeon.
* Metric: year-over-year growth of monthly value. Month-over-month change
  is dominated by seasonality and working-day noise, so it measures noise
  rather than co-movement; comparing each month with the same month a
  year earlier removes the seasonal pattern.
* Chart: Daejeon vs national YoY growth (top), and each region's
  correlation with the national YoY series (bottom).
* Output: output/KITA_monthly_4_yoy_vs_national.png
          output/KITA_monthly_4_yoy_vs_national.csv
====================================================================
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
from core.utils_chart import OUTPUT_DIR, PALETTE, save, use_korean_font
from core.utils_regions import ADJACENT_CONSISTENT, SCALE_GROUP

FILE_PATH = BASE_DIR / "data" / "processed" / "kita_regional_monthly_4_added.csv"
SAVE = "KITA_monthly_4_yoy_vs_national.png"

FOCUS = "대전"
NATION = "전국"
FLOWS = {"수출": "수출액_백만불", "수입": "수입액_백만불"}
LAG = 12


def load_monthly() -> pd.DataFrame:
    df = pd.read_csv(FILE_PATH, parse_dates=["연월"])
    # A partial final year would mix a few months into the yearly comparison.
    last_full_year = (
        df.groupby("연도")["연월"].nunique().loc[lambda s: s.eq(12)].index.max()
    )
    return df[df["연도"].le(last_full_year)]


def yoy_growth(df: pd.DataFrame, value_col: str, regions: list[str]) -> pd.DataFrame:
    wide = df.pivot_table(index="연월", columns="지역명", values=value_col)[regions]
    return wide.pct_change(LAG, fill_method=None).mul(100).dropna(how="all")


def correlation_table(df: pd.DataFrame, regions: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            flow: yoy_growth(df, col, regions + [NATION]).corr()[NATION].drop(NATION)
            for flow, col in FLOWS.items()
        }
    )


def plot(df: pd.DataFrame, corr: pd.DataFrame) -> None:
    fig, axes = plt.subplots(
        2, 2, figsize=(14, 8), layout="constrained", height_ratios=[1.4, 1]
    )
    for col_idx, (flow, value_col) in enumerate(FLOWS.items()):
        growth = yoy_growth(df, value_col, [FOCUS, NATION])
        ax = axes[0, col_idx]
        ax.plot(
            growth.index, growth[NATION], color=PALETTE["muted"], lw=1.4, label=NATION
        )
        ax.plot(
            growth.index, growth[FOCUS], color=PALETTE["accent"], lw=1.0, label=FOCUS
        )
        ax.axhline(0, color=PALETTE["text"], lw=0.8)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.set_title(
            f"{flow} 전년 동월 대비 증감률", loc="left", fontsize=11, fontweight="bold"
        )
        ax.legend(frameon=False, loc="upper left")

        ax = axes[1, col_idx]
        values = corr[flow].sort_values()
        colors = [
            PALETTE["accent"] if r == FOCUS else PALETTE["muted"] for r in values.index
        ]
        ax.barh(values.index, values, color=colors)
        for y, v in enumerate(values):
            ax.text(v + 0.01, y, f"{v:.2f}", va="center", fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_title(
            f"{flow}: 전국 증감률과의 상관계수",
            loc="left",
            fontsize=11,
            fontweight="bold",
        )
        ax.grid(axis="x", linestyle="--", alpha=0.35)

    start, end = df["연월"].min().year + 1, df["연월"].max().year
    fig.suptitle(
        f"대전·비교 지역 월별 수출입액 전년 동월 대비 증감률과 전국과의 상관, {start}~{end}",
        fontsize=14,
        fontweight="bold",
    )
    save(fig, SAVE)


if __name__ == "__main__":
    use_korean_font()
    monthly = load_monthly()
    regions = [FOCUS] + SCALE_GROUP + ADJACENT_CONSISTENT
    corr = correlation_table(monthly, regions)
    corr.round(2).to_csv(
        OUTPUT_DIR / SAVE.replace(".png", ".csv"), encoding="utf-8-sig"
    )
    print(corr.round(2).to_string())
    plot(monthly, corr)
