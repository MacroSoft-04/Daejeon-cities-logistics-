from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. File path configuration
base_dir = Path(".")
data_dir = base_dir / "NLIC" / "data"
save_dir = base_dir / "NLIC" / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# Korean font setup
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 2. Load data and convert units (to Millions)
df = pd.read_csv(data_dir / "yearly_total_amount.csv")
df["총 출발량(백만)"] = df["총 출발량"] / 1_000_000
df["총 도착량(백만)"] = df["총 도착량"] / 1_000_000

# 3. Multilingual configuration dictionary
I18N = {
    "ko": {
        "title_main": "연도별 총 출발량 및 총 도착량",
        "xlabel": "연도",
        "ylabel_1": "총 출발량 (백만 단위)",
        "ylabel_2": "총 도착량 (백만 단위)",
        "label_dep": "총 출발량(백만)",
        "label_arr": "총 도착량(백만)",
        "legend_title": "구분",
        "filename": "yearly_total_amount_ko.jpg",
        "year_fmt": lambda yr: f"{yr}년",
    },
    "en": {
        "title_main": "Yearly Total Departure & Arrival Freight Amount",
        "xlabel": "Year",
        "ylabel_1": "Total Departure (Millions)",
        "ylabel_2": "Total Arrival (Millions)",
        "label_dep": "Departure Amount",
        "label_arr": "Arrival Amount",
        "legend_title": "Category",
        "filename": "yearly_total_amount_en.jpg",
        "year_fmt": lambda yr: f"{yr}yr",
    },
}


# 4. Multilingual plot generation function
def generate_multilingual_plots(df, save_dir):
    for lang in ["ko", "en"]:
        cfg = I18N[lang]

        # Configure figure and dual Y-axes
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()

        # Set X-axis indices and bar widths
        x = np.arange(len(df["연도"]))
        width = 0.35
        x_labels = [cfg["year_fmt"](yr) for yr in df["연도"]]

        # Plot bar charts (Left: Departure volume, Right: Arrival volume)
        rect1 = ax1.bar(
            x - width / 2,
            df["총 출발량(백만)"],
            width,
            label=cfg["label_dep"],
            color="#87CEEB",
        )
        rect2 = ax2.bar(
            x + width / 2,
            df["총 도착량(백만)"],
            width,
            label=cfg["label_arr"],
            color="#FA8072",
        )

        # Automatically/Manually adjust Y-axis limits
        dep_max = df["총 출발량(백만)"].max()
        arr_max = df["총 도착량(백만)"].max()
        ax1.set_ylim(0, dep_max * 1.25)
        ax2.set_ylim(0, arr_max * 1.25)

        # Set axis labels and title
        plt.title(cfg["title_main"], fontsize=16, pad=20, fontweight="bold")
        ax1.set_xlabel(cfg["xlabel"], fontsize=12)
        ax1.set_ylabel(cfg["ylabel_1"], fontsize=12, color="#2E8B57")
        ax2.set_ylabel(cfg["ylabel_2"], fontsize=12, color="#CD5C5C")

        # Apply X-axis tick labels
        ax1.set_xticks(x)
        ax1.set_xticklabels(x_labels, fontsize=11)
        ax1.grid(axis="y", linestyle="--", alpha=0.4)

        # Annotate data values on top of bars
        for p in ax1.patches:
            height = p.get_height()
            if height > 0:
                ax1.text(
                    p.get_x() + p.get_width() / 2.0,
                    height + (dep_max * 0.02),
                    f"{height:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )

        for p in ax2.patches:
            height = p.get_height()
            if height > 0:
                ax2.text(
                    p.get_x() + p.get_width() / 2.0,
                    height + (arr_max * 0.02),
                    f"{height:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )

        # Combine legends from both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(
            lines1 + lines2,
            labels1 + labels2,
            title=cfg["legend_title"],
            loc="upper left",
            bbox_to_anchor=(1.08, 1.0),
            borderaxespad=0.0,
            fontsize=10,
        )

        # Save image
        save_path = save_dir / cfg["filename"]
        plt.savefig(
            save_path, dpi=300, bbox_inches="tight", pad_inches=0.3
        )
        plt.close()


# 5. Execute function
generate_multilingual_plots(df, save_dir)
