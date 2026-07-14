import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

csv_data = "grouping.csv"  # Path to the CSV file containing the data
plt.rcParams['font.family'] = 'Malgun Gothic'  # Set font to Malgun Gothic for Korean characters'
df = pd.read_csv(csv_data)

df["x_라벨"] = df["연도"].astype(str) + "년"  # Create a new column for x-axis labels by combining year and "년"

regions = ["수도권", "영남권", "충청권", "호남권", "기타"]  # List of regions to be plotted
ratio_cols = [f"{r}_비율" for r in regions]

def save_plot(data, title_suffix, filename):
    # extract the ratio data and set index
    plot_df = data.set_index("x_라벨")[ratio_cols]
    plot_df.columns = regions

    fig, ax = plt.subplots(figsize = (12, 7))
    plot_df.plot(kind="bar",stacked=True, ax=ax, cmap = "Set2", width = 0.6)

    # graph style
    plt.title(f"연도 및 구분별 권역 물동량 비율 변화({title_suffix})(2020~2023)", fontsize = 16, pad = 15)
    plt.xlabel("연도", fontsize = 12)
    plt.ylabel("물동량 비율(%)", fontsize = 12)
    plt.xticks(rotation=0)
    plt.grid(axis="y", linestyle="--", alpha = 0.5)

    #legend location
    plt.legend(title="권역", bbox_to_anchor=(1.02, 1), loc="upper left")

    for p in ax.patches:
        width, height = p.get_width(), p.get_height()
        x, y = p.get_xy()
        if height > 3:
            ax.text(
                x + width / 2,
                y + height / 2,
                f"{height:.1f}%",
                ha = "center",
                va = "center",
                fontsize = 10,
                color = "black",
                weight = "normal",
                )
    plt.savefig(filename, dpi = 300, bbox_inches="tight")
    plt.close()

# filter data and save to png
df_departure = df.loc[df["구분"]=="출발"]
save_plot(df_departure, "출발", "grouping_departure.png")

df_arrival = df.loc[df["구분"]=="도착"]
save_plot(df_arrival, "도착", "grouping_arrival.png")



