"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/tradedata_dj_2020_2025.csv (관세청 무역통계)
* Chart: exports above the axis, imports below, stacked by commodity group,
  with the trade balance drawn on the same scale. Splitting these into two
  charts hid the fact that the two sides are driven by different commodities.
* Grouping: the two flows are collapsed into one shared set of four groups.
  Ranking each side separately would put different commodities in the same
  colour and make the panels uncomparable.
* Output: output/02_trade_diverging.jpg
====================================================================
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
from core.utils_chart import PREP_FOOD, MEDIC_DEVICE, save, use_korean_font

data_dir = BASE_DIR / "data" / "processed"
FILE_PATH = data_dir / "tradedata_2000_2025_4_added.csv"

MILLION = 1_000  # source unit is thousand USD
LABEL_MIN_SHARE = 15

SECTION = ["조제식품류", "광학, 정밀, 의료기기"]

DJ = "대전광역시"

SAVE = "TD_08_DJ_prep_food_medic_divice.png"

use_korean_font()

df = pd.read_csv(FILE_PATH)
df = df[df["지역명"].eq(DJ) & df["부명약칭"].isin(SECTION)].copy()

DEBUG = True


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def check_shares_detail_rank(df: pd.DataFrame) -> dict:
    """Find the top chapter over the past 10 years based on average sectional import and export values."""
    frame = df[df["기간"].gt(2015)]
    results = {}
    for section in SECTION:
        section_frame = frame[frame["부명약칭"].eq(section)]
        year = section_frame.groupby(["류명약칭", "기간"], as_index=False)[
            ["수출금액", "수입금액"]
        ].sum()
        ex_ratio = year.groupby("류명약칭")["수출금액"].mean()
        im_ratio = year.groupby("류명약칭")["수입금액"].mean()

        debug_print(f"\n--- {section} ---")
        debug_print("\nExport Rank(2016~2025):")
        debug_print(ex_ratio.nlargest(5).to_string())
        debug_print("\nImport Rank(2016~2025):")
        debug_print(im_ratio.nlargest(5).to_string())

        results[section] = {
            "export": ex_ratio.nlargest(4).index.tolist(),
            "import": im_ratio.nlargest(4).index.tolist(),
        }
    return results


COLORS_BASIC = {"조제식품류": PREP_FOOD, "광학, 정밀, 의료기기": MEDIC_DEVICE}


def shares(
    frame: pd.DataFrame, val_col: str, group_col: str, groups: list[str]
) -> pd.DataFrame:
    """Each group's percent of the region's yearly total in the selected sections."""
    table = (
        frame.groupby(["기간", group_col])[val_col]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=groups, fill_value=0)
    )
    return table.div(table.sum(axis=1), axis=0) * 100


def plot_regions():
    """Plot exports above the axis, imports below, stacked by commodity group."""
    rankings = check_shares_detail_rank(df)
    all_groups = list(
        dict.fromkeys(
            group
            for section in SECTION
            for group in (rankings[section]["export"] + rankings[section]["import"])
        )
    )
    all_groups = list(dict.fromkeys(all_groups))
    fig, axes = plt.subplots(
        len(SECTION),
        1,
        figsize=(12, 3.2 * len(SECTION)),
        sharex=True,
        sharey=True,
        layout="constrained",
    )
    for ax, section in zip(axes, SECTION):
        colors = COLORS_BASIC[section]
        EX_GROUPS = rankings[section]["export"]
        IM_GROUPS = rankings[section]["import"]
        frame = df[df["부명약칭"].eq(section)].copy()
        frame["ex_group"] = frame["류명약칭"].where(frame["류명약칭"].isin(EX_GROUPS))
        frame["im_group"] = frame["류명약칭"].where(frame["류명약칭"].isin(IM_GROUPS))

        seen_labels = set()

        for table, groups, sign in (
            (shares(frame, "수출금액", "ex_group", EX_GROUPS), EX_GROUPS, 1),
            (
                shares(frame, "수입금액", "im_group", IM_GROUPS),
                IM_GROUPS,
                -1,
            ),
        ):
            bottom = np.zeros(len(table))

            for group in groups:
                values = table[group].to_numpy() * sign
                label = group if group not in seen_labels else None
                seen_labels.add(group)
                ax.bar(
                    table.index,
                    values,
                    bottom=bottom,
                    width=0.6,
                    color=colors,
                    edgecolor="white",
                    linewidth=0.8,
                    label=label,
                )
                ax.grid(True, axis="y", linestyle="--", alpha=0.35)
                for year, value, base, share in zip(
                    table.index, values, bottom, table[group]
                ):
                    if share < LABEL_MIN_SHARE:
                        continue
                    ax.text(
                        year,
                        base + value / 2,
                        f"{share:.0f}%",
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="white",
                    )
                bottom += values
        ax.axhline(0, color="#1c1c1c", linewidth=1)
        ax.yaxis.set_major_formatter(lambda v, _: f"{abs(v):.0f}%")
        ax.set_title(section, loc="left", fontsize=10, fontweight="bold")

    group_colors = {
        group: color
        for section in SECTION
        for group, color in COLORS_BASIC[section].items()
    }

    handles = [plt.Rectangle((0, 0), 1, 1, color=group_colors[g]) for g in all_groups]
    fig.suptitle(
        f"대전광역시 {section} 수출입 품목 구성"
        f"{df['기간'].min()}~{df['기간'].max()}",
        y=0.99,
        fontsize=15,
        fontweight="bold",
    )
    fig.legend(
        handles,
        all_groups,
        loc="outside upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=4,
        frameon=False,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, SAVE)


if __name__ == "__main__":
    plot_regions()
