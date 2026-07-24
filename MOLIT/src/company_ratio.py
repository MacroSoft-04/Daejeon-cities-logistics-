from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# 1. Path settings
base_dir = Path(".")
data_dir = base_dir / "MOLIT" / "data"
save_dir = base_dir / "MOLIT" / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# Load the SQL execution result dataset
# Expected columns: ['YEAR', 'COMPANY_NAME', 'REGISTRATION_COUNT']
df = pd.read_csv(data_dir / "company_ratio.csv")

# Korean font configuration
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# Company Name Translation Dictionary (Korean -> Official English)
COMPANY_MAP_EN = {
    # Major Logistics & Fulfillment
    "롯데글로벌로지스": "Lotte Global Logistics",
    "비지에프로지스": "BGF Logistics",
    "씨제이대한통운": "CJ Logistics",
    "코업로지스틱스": "Co-op Logistics",
    "농협물류": "NongHyup Logistics",
    "용마로지스": "Yongma Logis",
    "한국농수산식품유통공사": "aT (Korea Agro-Fisheries)",
    "한진": "Hanjin",
    "한스에프앤엘": "Hans F&L",
    "오뚜기물류서비스": "Ottogi Logistics Service",
    "쿠팡로지스틱스서비스": "CPLB (Coupang Logistics)",
    "쿠팡풀필먼트서비스": "CFS (Coupang Fulfillment)",
    "라인물류시스템": "Line Logistics System",
    "에스로지스틱스": "S-Logistics",
    "한솔로지스틱스": "Hansol Logistics",
    "삼성전로지텍": "Samsung Electronics Logitech",
}

# 2. Multilingual configuration dictionary
I18N = {
    "ko": {
        "title_main": "연도별 물류창고 등록 상위 기업 (Top 5)",
        "xlabel": "등록 건수",
        "ylabel": "기업명",
        "filename": "company_ratio_ko.jpg",
    },
    "en": {
        "title_main": "Top 5 Warehouse Registration Companies by Year",
        "xlabel": "Registration Count",
        "ylabel": "Company Name",
        "filename": "company_ratio_en.jpg",
    },
}


# 3. Multilingual subplot generation function
def generate_top_companies_plot(df, save_dir):
    years = sorted(df["YEAR"].unique())
    num_years = len(years)

    for lang in ["ko", "en"]:
        cfg = I18N[lang]

        # Calculate grid layout dynamically (e.g., 2 rows x 3 cols for 6 years)
        cols = 3
        rows = int(np.ceil(num_years / cols))

        fig, axes = plt.subplots(
            rows, cols, figsize=(16, 4 * rows), sharex=False
        )
        axes = axes.flatten()

        for idx, yr in enumerate(years):
            ax = axes[idx]
            # Filter top 5 data for the specific year
            df_year = df[df["YEAR"] == yr].sort_values(
                by="REGISTRATION_COUNT", ascending=True
            )

            # Apply English translation dynamically if language is set to 'en'
            if lang == "en":
                company_labels = df_year["COMPANY_NAME"].map(
                    COMPANY_MAP_EN
                )
                # Fallback to Korean name if not found in dictionary
                company_labels = company_labels.fillna(
                    df_year["COMPANY_NAME"]
                )
            else:
                company_labels = df_year["COMPANY_NAME"]

            # Draw horizontal bar chart
            bars = ax.barh(
                company_labels,
                df_year["REGISTRATION_COUNT"],
                color="#38A3CE",
                height=0.6,
            )

            # Subplot titles & styling
            ax.set_title(f"[{yr}]", fontsize=14, fontweight="bold", pad=10)
            ax.set_xlabel(cfg["xlabel"], fontsize=10)
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            ax.set_axisbelow(True)

            # Adjust X-axis limit to prevent label truncation
            max_val = (
                df_year["REGISTRATION_COUNT"].max()
                if not df_year.empty
                else 1
            )
            ax.set_xlim(0, max_val * 1.25)

            # Annotate exact count on each bar
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax.text(
                        width + (max_val * 0.02),
                        bar.get_y() + bar.get_height() / 2.0,
                        f"{int(width):,}건"
                        if lang == "ko"
                        else f"{int(width):,}",
                        ha="left",
                        va="center",
                        fontsize=9,
                        fontweight="bold",
                    )

        # Hide any unused subplots
        for j in range(idx + 1, len(axes)):
            fig.delaxes(axes[j])

        # Figure super title
        fig.suptitle(
            cfg["title_main"], fontsize=18, fontweight="bold", y=0.98
        )
        plt.tight_layout(rect=[0, 0, 1, 0.96])

        # Save image
        save_path = save_dir / cfg["filename"]
        plt.savefig(
            save_path, dpi=300, bbox_inches="tight", pad_inches=0.2
        )
        plt.close(fig)


# 4. Execute function
generate_top_companies_plot(df, save_dir)