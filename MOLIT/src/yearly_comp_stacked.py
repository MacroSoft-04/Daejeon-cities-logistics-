from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# 1. Path Settings
base_dir = Path(".")
data_dir = base_dir / "MOLIT" / "data"
save_dir = base_dir / "MOLIT" / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 2. Load Datasets
df_ratio = pd.read_csv(data_dir / "company_ratio.csv")
df_total = pd.read_csv(data_dir / "yearly_total.csv")

# Korean font setup
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# Company Name Translation Dictionary
# Dictionary structure: "Search Key (Original Korean)": ["English Name", "Korean Display Name", "Primary Brand Color HEX"]
COMPANY_INFO = {
    # Major Logistics & Fulfillment Companies
    "CJ대한통운": ["CJ Logistics", "CJ대한통운"],
    "롯데글로벌로지스": ["Lotte Global Logistics", "롯데글로벌로지스"],
    "쿠팡풀필먼트": ["Coupang Fulfillment Services", "쿠팡풀필먼트"],
    "쿠팡로지스틱스": ["Coupang Logistics Services", "쿠팡로지스틱스"],
    "지에스네트웍스": ["GS Networks", "지에스네트웍스"],
    "오뚜기물류서비스": ["Ottogi Logistics Service", "오뚜기물류서비스"],
    
    # Fallback / Exception handling for "Others"
    "기타": ["Others", "기타"],
}

COLOR_PALETTE = [
    "#6694C6",  
    "#F28E2B",  
    "#E15759",  
    "#76B7B2",  
    "#59A14F",  
    "#EDC948",  
    "#B07AA1",  
    "#FF9DA7",  
    "#9C755F",  
    "#BAB0AC",  
]

# Multilingual configuration dictionary
I18N = {
    "ko": {
        "title": "Yearly Warehouse Registrations & Top Company Breakdown",
        "xlabel": "Year",
        "ylabel": "Registration Count (Scaled Others)",
        "others": "기타 (Others)",
        "legend_title": "Rank",
        "filename": "yearly_company_stacked_ko.jpg",
    },
    "en": {
        "title": "Yearly Warehouse Registrations & Top Company Breakdown",
        "xlabel": "Year",
        "ylabel": "Registration Count (Scaled Others)",
        "others": "Others",
        "legend_title": "Rank",
        "filename": "yearly_company_stacked_en.jpg",
    },
}

class ColorMapper:
    def __init__(self, palette):
        self.palette = palette
        self.color_map = {"기타": "#E0E0E0", "Others": "#E0E0E0"}  
        self.color_idx = 0

    def get_color(self, comp_name):
        if comp_name not in self.color_map:
            # if company name is not in the color map, assign a new color
            self.color_map[comp_name] = self.palette[self.color_idx % len(self.palette)]
            self.color_idx += 1
        return self.color_map[comp_name]

# example: ColorMapper(COLOR_PALETTE)
color_mapper = ColorMapper(COLOR_PALETTE)

def get_company_info(comp_name, lang='ko'):
    if comp_name in COMPANY_INFO:
        en_name, ko_name = COMPANY_INFO[comp_name]
        name = en_name if lang == "en" else ko_name
        return name
    else:
        # Fallback handling for companies not listed in the dictionary
        return comp_name
    
# 3. Data Processing Function (auto-calculation of 'Others' category)
def prepare_stacked_data(df_ratio, df_total):
    processed_records = []
    years = sorted(df_ratio["YEAR"].unique())

    for yr in years:
        threshold = 10

        # get total count for the year
        tot_sub = df_total[df_total["YEAR"] == yr]
        total_cnt = tot_sub["REGISTRATION_COUNT"].values[0] if not tot_sub.empty else 0

        # upper 5 companies
        top5 = df_ratio[df_ratio["YEAR"] == yr].sort_values(
            by="REGISTRATION_COUNT", ascending=False
        )
        top5_filtered = top5[top5["REGISTRATION_COUNT"] >= threshold]
        top5_sum = 0

        for rank, (_, row) in enumerate(top5_filtered.iterrows(), start=1):
            comp = row["COMPANY_NAME"]
            cnt = row["REGISTRATION_COUNT"]
            top5_sum += cnt
            ratio = (cnt / total_cnt) * 100 if total_cnt > 0 else 0

            processed_records.append(
                {
                    "YEAR": yr,
                    "CATEGORY": f"Top_{rank}",
                    "COMPANY_NAME": comp,
                    "COUNT": cnt,
                    "RATIO": ratio,
                }
            )

        # calculate 'Others' category
        others_cnt = max(0, total_cnt - top5_sum)
        others_ratio = (others_cnt / total_cnt) * 100 if total_cnt > 0 else 0

        processed_records.append(
            {
                "YEAR": yr,
                "CATEGORY": "Others",
                "COMPANY_NAME": "기타",
                "COUNT": others_cnt,
                "RATIO": others_ratio,
            }
        )
    return pd.DataFrame(processed_records)

# 4. Plot Function
def plot_zoomed_stacked_chart(df_ratio, df_total, save_dir):
    df_stacked = prepare_stacked_data(df_ratio, df_total)
    years = sorted(df_stacked["YEAR"].unique())

    for lang in ["ko", "en"]:
        cfg = I18N[lang]
        fig, ax = plt.subplots(figsize=(12, 7.5))

        bottoms = np.zeros(len(years))
        categories = ["Top_1", "Top_2", "Top_3", "Top_4", "Top_5", "Others"]

        # 'Others' category height scaling
        OTHERS_SCALE = 0.15
        
        # stack bar plot for each category
        for idx, cat in enumerate(categories):
            plot_heights = []
            labels = []
            segment_colors = []

            for yr in years:
                sub = df_stacked[
                    (df_stacked["YEAR"] == yr)
                    & (df_stacked["CATEGORY"] == cat)
                ]
                if not sub.empty:
                    cnt = sub["COUNT"].values[0]
                    ratio = sub["RATIO"].values[0]
                    comp = sub["COMPANY_NAME"].values[0]
                    name = get_company_info(comp, lang=lang)
                    h = cnt * OTHERS_SCALE if cat == "Others" else cnt
                    plot_heights.append(h)
                    segment_colors.append(color_mapper.get_color(comp))
                    labels.append((name, cnt, ratio))
                else:
                    plot_heights.append(0)
                    segment_colors.append('#E0E0E0')
                    labels.append(("", 0, 0.0))

            plot_heights = np.array(plot_heights)

            # Stacked Bar plot
            bars = ax.bar(
                [f"{yr}yr" if lang == "en" else f"{yr}년" for yr in years],
                plot_heights,
                bottom=bottoms,
                color=segment_colors,
                width=0.55,
                edgecolor="white",
                linewidth=0.8,
            )

            # add inner text labels
            for b_idx, (bar, (comp_name, real_cnt, ratio_val)) in enumerate(
                zip(bars, labels)
            ):
                if real_cnt > 0:
                    y_pos = bottoms[b_idx] + (plot_heights[b_idx] / 2.0)

                    if idx < 5:  # Top 1~5 companies
                        text_label = f"{comp_name}\n({ratio_val:.1f}%)\n{real_cnt}"
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            y_pos,
                            text_label,
                            ha="center",
                            va="center",
                            fontsize=7.5,
                            fontweight="bold",
                            color="black",
                            linespacing=1,
                        )
                    else:  # gray area for 'Others'
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            y_pos,
                            f"Others: {real_cnt}"
                            if lang == "en"
                            else f"기타: {real_cnt}",
                            ha="center",
                            va="center",
                            fontsize=8.5,
                            fontweight="bold",
                            color="#444444",
                        )

            bottoms += plot_heights

        # Add Total Amount annotations above each bar
        for idx, yr in enumerate(years):
            tot_sub = df_total[df_total["YEAR"] == yr]
            if not tot_sub.empty:
                tot_count = tot_sub["REGISTRATION_COUNT"].values[0]
                ax.text(
                    idx,
                    bottoms[idx] + (max(bottoms) * 0.02),
                    f"Total: {tot_count:,}",
                    ha="center",
                    va="bottom",
                    fontsize=9.5,
                    fontweight="bold",
                    color="#111111",
                )

        # Chart Title & Comment
        title_text = cfg["title"]
        ax.set_title(title_text, fontsize=15, pad=25, fontweight="bold")

        ax.text(
            0.01,
            0.98,
            "* 'Others' bar height is scaled down to 15% for Top 5 visibility",
            transform=ax.transAxes,
            fontsize=9,
            color="#666666",
            style="italic",
        )

        ax.set_xlabel(cfg["xlabel"], fontsize=11, labelpad=8)
        ax.set_ylabel(cfg["ylabel"], fontsize=11, labelpad=8)
        ax.set_ylim(0, max(bottoms) * 1.12)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)

        # 저장
        save_path = save_dir / cfg["filename"]
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight", pad_inches=0.2)
        plt.close(fig)


# 5. Execute
plot_zoomed_stacked_chart(df_ratio, df_total, save_dir)