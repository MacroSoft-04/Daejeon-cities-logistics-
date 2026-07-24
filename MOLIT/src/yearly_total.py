from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. File path configuration
base_dir = Path(".")
data_dir = base_dir / "MOLIT" / "data"
save_dir = base_dir / "MOLIT" / "output"
save_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(data_dir / "yearly_total.csv")

# Korean font setup
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 3. Multilingual configuration dictionary
I18N = {
    "ko": {
        "title_main": "연도별 물류창고 등록 수",
        "xlabel": "연도",
        "ylabel": "등록 수 (건)",
        "filename": "yearly_total_amount_ko.jpg",
        "year_fmt": lambda yr: f"{yr}년",
    },
    "en": {
        "title_main": "Yearly Total Warehouse Registration Count",
        "xlabel": "Year",
        "ylabel": "Registration Count",
        "filename": "yearly_total_amount_en.jpg",
        "year_fmt": lambda yr: f"{yr} yr",
    },
}


# 4. Multilingual plot generation function
def generate_multilingual_plots(df, save_dir):
    for lang in ["ko", "en"]:
        cfg = I18N[lang]

        # Configure figure
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Set X-axis indices and bar width
        x = np.arange(len(df["YEAR"]))
        width = 0.45  # single bar에 적합한 두께로 조절
        x_labels = [cfg["year_fmt"](yr) for yr in df["YEAR"]]

        # Plot bar charts (Center-aligned single bar)
        rects = ax1.bar(
            x,  
            df["REGISTRATION_COUNT"],
            width,
            color="#38A3CE",
            edgecolor="none",
        )

        # Set axis labels and title
        ax1.set_title(
            cfg["title_main"], fontsize=16, pad=20, fontweight="bold"
        )
        ax1.set_xlabel(cfg["xlabel"], fontsize=12, labelpad=10)
        ax1.set_ylabel(cfg["ylabel"], fontsize=12, labelpad=10)

        # Apply X-axis tick labels
        ax1.set_xticks(x)
        ax1.set_xticklabels(x_labels, fontsize=11)

        max_val = df["REGISTRATION_COUNT"].max()
        ax1.set_ylim(0, max_val * 1.15)

        ax1.grid(axis="y", linestyle="--", alpha=0.4)
        ax1.set_axisbelow(True) 

        # Annotate data values on top of bars 
        for p in ax1.patches:
            height = p.get_height()
            if height > 0:
                ax1.text(
                    p.get_x() + p.get_width() / 2.0,
                    height + (max_val * 0.015),  #
                    f"{int(height):,}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                )

        plt.tight_layout()

        # Save image
        save_path = save_dir / cfg["filename"]
        plt.savefig(
            save_path, dpi=300, bbox_inches="tight", pad_inches=0.2
        )
        plt.close(fig)


# 5. Execute function
generate_multilingual_plots(df, save_dir)