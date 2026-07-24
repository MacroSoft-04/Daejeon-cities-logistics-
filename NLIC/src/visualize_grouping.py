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
df = pd.read_csv(data_dir / "grouping.csv")

df.columns = df.columns.str.replace('"', "").str.strip()

# 2. Extract Columns Automatically from Dataframe
ko_ratio_cols = [c for c in df.columns if c.endswith("_비율")]
en_ratio_cols = [c for c in df.columns if c.endswith("_ratio")]

ko_labels = [c.replace("_비율", "") for c in ko_ratio_cols]
en_labels = [c.replace("_ratio", "").replace("_"," ") for c in en_ratio_cols]

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# Multilingual text dictionary
I18N = {
    "ko": {
        "title_main": "연도 및 구분별 물동량 비율 변화 (2019-2023)",
        "title_sub": "{type}",
        "type_map": {"출발": "출발", "도착": "도착"},
        "ratio_col": ko_ratio_cols,
        "region_labels": ko_labels,
        "legend_title": "권역",
        "xlabel": "연도",
        "ylabel": "물동량 비율(%)",
        "filename": "grouping_ko.jpg",
        "year_fmt": lambda yr: f"{yr}년",
    },
    "en": {
        "title_main": "year and region-based freight flow ratio change (2019-2023)",
        "region_col": "region_en",
        "title_sub": "{type}",
        "type_map": {"출발": "departure", "도착": "arrival"},
        "ratio_col": en_ratio_cols,
        "region_labels": en_labels,
        "legend_title": "Region",
        "xlabel": "Year",
        "ylabel": "car freight flow ratio (%)",
        "filename": "grouping_en.jpg",
        "year_fmt": lambda yr: f"{yr}year",
    },
}

# Subplot Title Color Mapping for Departure/Arrival
type_color_map = {"출발": "#17669e", "도착": "#ad5100"}
set2_colors = plt.cm.Set2.colors


# 3. Plotting Function supporting Multilingual Switch
def generate_multilingual_plots(df, save_dir):
    for lang in ["ko", "en"]:
        cfg = I18N[lang]

        # Prepare year labels for x-axis per language
        plot_df_base = df.copy()
        plot_df_base["x_label"] = plot_df_base["연도"].apply(cfg["year_fmt"])

        ratio_cols = cfg["ratio_col"]
        region_labels = cfg["region_labels"]

        fig, axes = plt.subplots(
            figsize=(24, 7), ncols=2, gridspec_kw={"wspace": 0.15}
        )
        handles, labels = [], []

        for i, gubun in enumerate(["출발", "도착"]):
            filtered_df = plot_df_base[plot_df_base["구분"] == gubun]
            ax = axes[i]

            # Adjust background color palette dynamically
            hue_offset = i * 0.03
            adjust_colors = []
            for color in set2_colors[: len(region_labels)]:
                hsv = mcolors.rgb_to_hsv(color[:3])
                hsv[0] = (hsv[0] + hue_offset) % 1.0
                adjust_colors.append(mcolors.hsv_to_rgb(hsv))

            # use the same colors as Set2 but replace the last one with a light gray
            custom_colors = list(set2_colors[: len(region_labels) - 1]) + ["#D1D5DB"]


            # Extract ratio data & map column display names for legend
            plot_df = filtered_df.set_index("x_label")[ratio_cols]
            plot_df.columns = cfg["region_labels"]

            # Render stacked bar plot
            plot_df.plot(
                kind="bar",
                stacked=True,
                ax=ax,
                width=0.6,
                legend=False,
                color=custom_colors,
            )

            if i == 0:
                handles, labels = ax.get_legend_handles_labels()

            # Apply Subtitle and Axis labels
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
            ax.set_ylabel(cfg["ylabel"], fontsize=12)
            ax.set_xticks(range(len(plot_df)))
            ax.set_xticklabels(plot_df.index, rotation=0)
            ax.grid(axis="y", linestyle="--", alpha=0.5)

            # Add percentage text on top/inside bars
            for p in ax.patches:
                width, height = p.get_width(), p.get_height()
                x, y = p.get_xy()
                if height > 0:
                    if height > 3:
                        ax.text(
                            x + width / 2,
                            y + height / 2,
                            f"{height:.1f}%",
                            ha="center",
                            va="center",
                            fontsize=10,
                            color="black",
                        )
                    else:
                        ax.text(
                            x + width / 2,
                            y + height + 0.6,
                            f"{height:.1f}%",
                            ha="center",
                            va="bottom",
                            fontsize=8,
                            color="dimgray",
                            weight="bold",
                        )

        # Main Title & Legend Styling
        fig.suptitle(cfg["title_main"], fontsize=20, y=1.05, fontweight="bold")
        fig.legend(
            handles,
            labels,
            title=cfg["legend_title"],
            loc="center",
            bbox_to_anchor=(0.9, 0.75),
            fontsize=12,
            title_fontsize=13,
        )

        fig.subplots_adjust(left=0.08, right=0.86, wspace=0.35)

        # Save visualization
        save_path = save_dir / cfg["filename"]
        plt.savefig(
            save_path, dpi=300, bbox_inches="tight", pad_inches=0.4
        )
        plt.close()
generate_multilingual_plots(df, save_dir)
