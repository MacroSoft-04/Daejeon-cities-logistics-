import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path
import matplotlib.colors as mcolors

csv_data = "NLIC/data/grouping.csv"  # Path to the CSV file containing the data
plt.rcParams['font.family'] = 'Malgun Gothic'  # Set font to Malgun Gothic for Korean characters'
df = pd.read_csv(csv_data)

type_data = {'출발' : "#17669e", '도착' : "#ad5100"}

df["x_라벨"] = df["연도"].astype(str) + "년"  # Create a new column for x-axis labels by combining year and "년"

regions = ["수도권", "영남권", "충청권", "호남권", "기타"]  # List of regions to be plotted
ratio_cols = [f"{r}_비율" for r in regions]

set2_colors = plt.cm.Set2.colors

# save directory
save_dir = Path("NLIC/output")
save_dir.mkdir(parents=True, exist_ok=True)

# Separate visualization for '출발' (Departure) and '도착' (Arrival)
def save_plot(df, regions, ratio_cols, save_path):

    fig, axes = plt.subplots(figsize = (24, 7), ncols=2, gridspec_kw={'wspace': 0.15})
    handles, labels = [], []

    for i, data in enumerate(type_data):
        filtered_df = df[df["구분"] == data]
        ax = axes[i]

        # Set the color palette for the background of the plot
        hue_offset = i * 0.03
        adjust_colors = []
        for color in set2_colors:
            hsv = mcolors.rgb_to_hsv(color[:3])
            
            hsv[0] = (hsv[0] + hue_offset) % 1.0 
            adjust_colors.append(mcolors.hsv_to_rgb(hsv))

        set2_custom = mcolors.ListedColormap(adjust_colors)

        # extract the ratio data and set index
        plot_df = filtered_df.set_index("x_라벨")[ratio_cols]
        plot_df.columns = regions
        plot_df.plot(kind="bar",stacked=True, ax=ax, width = 0.6, legend=False, cmap=set2_custom)

        if i == 0:
            handles, labels = ax.get_legend_handles_labels()
        # graph style
        ax.set_title(f"연도 및 구분별 권역 물동량 비율 변화({data})(2020~2023)", 
                     y = 1.03, fontsize = 16, 
                     pad = 3, 
                     color=type_data[data],
                     weight = "bold")
        ax.set_xlabel("연도", fontsize = 12)
        ax.set_ylabel("물동량 비율(%)", fontsize = 12)
        ax.set_xticks(range(len(plot_df)))
        ax.set_xticklabels(plot_df.index, rotation = 0)
        ax.grid(axis="y", linestyle="--", alpha = 0.5)

        for p in ax.patches:
            width, height = p.get_width(), p.get_height()
            x, y = p.get_xy()
            if height > 0:  # Only label bars that actually have data
                if height > 3:
                    # Large areas: Place text right in the center of the bar
                    ax.text(
                        x + width / 2,
                        y + height / 2,
                        f"{height:.1f}%",
                        ha="center",
                        va="center",
                        fontsize=10,
                        color="black"
                    )
                else:
                    # Tiny areas (like 기타): Place text slightly ABOVE the segment so it's readable
                    ax.text(
                        x + width / 2,
                        y + height + 0.6,  # Shifted up by 0.5
                        f"{height:.1f}%",
                        ha="center",
                        va="bottom",       # Align bottom of text to the top of the bar
                        fontsize=8,        # Made slightly smaller so it fits cleanly
                        color="dimgray",   # Muted color so it doesn't look cluttered
                        weight="bold"
                    )
    #legend location
    fig.legend(
        handles, 
        labels, 
        title="권역", 
        loc="center", 
        bbox_to_anchor=(0.9, 0.75), # Positions it exactly in the middle of the figure
        fontsize=12,
        title_fontsize=13
    )
    fig.suptitle("권역별 물동량 비율 변화", fontsize=20, y=1.05)
    fig.subplots_adjust(left=0.08, right=0.86, wspace=0.35)
    save_path = save_dir / f"grouping.jpg"
    plt.savefig(save_path, dpi = 300, bbox_inches="tight", pad_inches=0.4)
    plt.close()
save_plot(df, regions, ratio_cols, save_dir)