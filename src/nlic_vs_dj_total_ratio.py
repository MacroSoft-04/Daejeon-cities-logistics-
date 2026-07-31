import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path
import matplotlib.colors as mcolors

# save directory
base_dir = Path("./NLIC")
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# Path to the CSV file containing the data
data_dir = base_dir / "data"

# 1. Load both dataframes
df_ratios = pd.read_csv(data_dir / "Deajeon_grouping.csv")
df_totals = pd.read_csv(data_dir / "Deajeon_yearly_total_amount.csv")

# Convert totals to Millions
df_totals["출발_백만"] = df_totals["총 출발량"] / 1_000_000
df_totals["도착_백만"] = df_totals["총 도착량"] / 1_000_000

# 2. Extract Columns Automatically from Dataframe
ko_ratio_cols = [c for c in df_ratios.columns if c.endswith("_비율")]
en_ratio_cols = [c for c in df_ratios.columns if c.endswith("_ratio")]

ko_labels = [c.replace("_비율", "") for c in ko_ratio_cols]
en_labels = [c.replace("_ratio", "").replace("_"," ") for c in en_ratio_cols]


plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

type_color_map = {"출발": "#17669e", "도착": "#ad5100"}
set2_colors = plt.cm.Set2.colors

# Multilingual text dictionary
I18N = {
    "ko": {
        "title_main": "대전 기준 연도·권역별 물동량 비율 변화 (2019-2023)",
        "title_sub": "{type}",
        "type_map": {"출발": "출발", "도착": "도착"},
        "ratio_col": ko_ratio_cols,
        "region_labels": ko_labels,
        "legend_title": "권역",
        "xlabel": "연도",
        "ylabel": "물동량 비율(%)",
        "filename": "Deajeon_total_ratio_ko.jpg",
        "year_fmt": lambda yr: f"{yr}년",
    },
    "en": {
        "title_main": "Freight Flow Ratio Change by Region for Deajeon (2019-2023)",
        "region_col": "region_en",
        "title_sub": "{type}",
        "type_map": {"출발": "departure", "도착": "arrival"},
        "ratio_col": en_ratio_cols,
        "region_labels": en_labels,
        "legend_title": "Region",
        "xlabel": "Year",
        "ylabel": "car freight flow ratio (%)",
        "filename": "Deajeon_total_ratio_en.jpg",
        "year_fmt": lambda yr: f"{yr}year",
    },
}

def generate_multilingual_plots(df_ratios, df_totals, save_dir):
    for lang in ["ko", "en"]:
        cfg = I18N[lang]

        ratio_cols = cfg["ratio_col"]
        region_labels = cfg["region_labels"]

        # Prepare base dataframe with language-specific x-axis labels
        plot_df_base = df_ratios.copy()
        plot_df_base["x_label"] = plot_df_base["연도"].apply(cfg["year_fmt"])

        fig, axes = plt.subplots(
            figsize=(20, 8), ncols=2, gridspec_kw={"wspace": 0.25}
        )
        handles, labels = [], []

        for i, gubun in enumerate(["출발", "도착"]):
            ax = axes[i]
            filtered_df = plot_df_base[plot_df_base["구분"] == gubun].copy()
            total_col_m = "출발_백만" if gubun == "출발" else "도착_백만"

            # Merge total values per year (in Millions)
            filtered_df = filtered_df.merge(
                df_totals[["연도", total_col_m]], on="연도", how="left"
            )

            # 1. Convert percentages to Absolute Values (in Millions)
            abs_cols = []
            for col in ratio_cols:
                abs_col_name = f"{col}_abs"
                filtered_df[abs_col_name] = (
                    filtered_df[col] / 100
                ) * filtered_df[total_col_m]
                abs_cols.append(abs_col_name)

            # 2. Build plotting DataFrame
            plot_df = filtered_df.set_index("x_label")[abs_cols]
            plot_df.columns = region_labels

            # Custom colors: Set2 palette + Light Gray for 'Others'
            custom_colors = list(set2_colors[: len(region_labels) - 1]) + ["#D1D5DB"]

            # 3. Plot absolute stacked bar chart
            plot_df.plot(
                kind="bar",
                stacked=True,
                ax=ax,
                width=0.6,
                legend=False,
                color=custom_colors,
            )

            # Calculate yearly total sums per bar stack to compute segment percentages
            bar_totals = plot_df.sum(axis=1).values

            # 4. Add percentage labels inside stacked bar segments
            for p in ax.patches:
                width, height = p.get_width(), p.get_height()
                x, y = p.get_xy()

                # Determine which bar index (x-axis category) this patch belongs to
                bar_idx = int(round(x + width / 2))
                if 0 <= bar_idx < len(bar_totals) and bar_totals[bar_idx] > 0:
                    pct = (height / bar_totals[bar_idx]) * 100

                    if pct >= 4.0:  # Display label inside segment if large enough
                        ax.text(
                            x + width / 2,
                            y + height / 2,
                            f"{pct:.1f}%",
                            ha="center",
                            va="center",
                            fontsize=9,
                            color="black",
                        )
                    elif pct >= 0:  # Display label slightly outside/above segment
                        ax.text(
                            x + width / 2,
                            y + height + (bar_totals[bar_idx] * 0.005),
                            f"{pct:.1f}%",
                            ha="center",
                            va="bottom",
                            fontsize=7.5,
                            color="dimgray",
                            weight="bold",
                        )

            # 5. Add Total Amount annotations above each bar
            max_bar_height = max(bar_totals) if len(bar_totals) > 0 else 100

            for idx, yr in enumerate(filtered_df["연도"].unique()):
                tot_val = df_totals[df_totals["연도"] == yr][total_col_m].values[0]
                total_text = (
                    f"Total: {tot_val:.1f}M"
                    if lang == "en"
                    else f"총합: {tot_val:.1f}백만"
                )

                # Place text dynamic relative to the total height of each specific bar
                current_stack_top = bar_totals[idx]
                ax.text(
                    idx,
                    current_stack_top + (max_bar_height * 0.04),
                    total_text,
                    ha="center",
                    va="bottom",
                    fontsize=10.5,
                    fontweight="bold",
                    color=type_color_map[gubun],
                )

            # 6. Formatting, Titles, & Labels
            type_text = cfg["type_map"][gubun]
            sub_title = cfg["title_sub"].format(type=type_text)

            ax.set_title(
                sub_title,
                y=1.03,
                fontsize=16,
                pad=3,
                color=type_color_map[gubun],
                weight="bold",
            )
            ax.set_xlabel(cfg["xlabel"], fontsize=12)
            ax.xaxis.set_label_coords(0.5, -0.08)

            # Y-axis label reflecting Million unit values
            y_label_text = (
                "Freight Flow Amount (Million Tons)"
                if lang == "en"
                else "물동량 (백만 톤)"
            )
            ax.set_ylabel(y_label_text, fontsize=12)

            # Dynamic Y-axis upper limit to make room for annotations
            ax.set_ylim(0, max_bar_height * 1.15)
            ax.set_xticklabels(plot_df.index, rotation=0)
            ax.grid(axis="y", linestyle="--", alpha=0.5)

            if i == 0:
                handles, labels = ax.get_legend_handles_labels()

        # Figure Level Title & Legend
        fig.suptitle(cfg["title_main"], fontsize=18, y=1.02, fontweight="bold")
        fig.legend(
            handles,
            labels,
            title=cfg["legend_title"],
            loc="center left",
            bbox_to_anchor=(0.91, 0.5),
            fontsize=11,
            title_fontsize=12,
        )

        fig.subplots_adjust(left=0.08, right=0.88, wspace=0.25)

        # Save Plot
        save_path = save_dir / cfg["filename"]
        plt.savefig(save_path, dpi=300, bbox_inches="tight", pad_inches=0.3)
        plt.close()

# Execute script
generate_multilingual_plots(df_ratios, df_totals, save_dir)