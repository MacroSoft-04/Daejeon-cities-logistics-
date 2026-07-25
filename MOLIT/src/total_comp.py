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
    "롯데글로벌로지스": ["Lotte Global Logistics", "롯데글로벌로지스", "#FF8DB1"],
    "비지에프로지스": ["BGF Logistics", "비지에프로지스", "#00A859"],
    "씨제이대한통운": ["CJ Logistics", "CJ대한통운", "#FCA452"],
    "일죽창고": ["IlJuk Warehouse", "일죽창고", "#4A6572"],
    "동원로엑스": ["Dongwon LOEX", "동원로엑스", "#2CA02C"],
    "컬리넥스트마일": ["Kurly Nextmile", "컬리넥스트마일", "#5F0080"],
    "한솔로지스": ["Hansol Logistics", "한솔로지스", "#34495E"],
    "진성비에프": ["Jinsung BF", "진성비에프", "#E67E22"],
    "농협물류": ["NongHyup Logistics", "농협물류", "#00833E"],
    "용마로지스": ["Yongma Logis", "용마로지스", "#16A085"],
    "한국농수산식품유통공사": ["aT (Korea Agro-Fisheries)", "한국농수산식품유통공사", "#27AE60"],
    "한진": ["Hanjin", "한진", "#1F77B4"],
    "한스에프앤엘": ["Hans F&L", "한스에프앤엘", "#8E44AD"],
    "오뚜기물류서비스": ["Ottogi Logistics Service", "오뚜기물류서비스", "#FAD43E"],
    "쿠팡로지스서비스": ["CPLB (Coupang Logistics)", "쿠팡로지스틱스", "#26B3EB"],
    "쿠팡풀필먼트서비스": ["CFS (Coupang Fulfillment)", "쿠팡풀필먼트", "#8BF96C"],
    "라인물류시스템": ["Line Logistics System", "라인물류시스템", "#2980B9"],
    "에스로지스": ["S-Logistics", "에스로지스틱스", "#9B59B6"],
    "한솔로지스": ["Hansol Logistics", "한솔로지스틱스", "#34495E"],
    "삼성전로지텍": ["Samsung Electronics Logitech", "삼성전자로지텍", "#034EA2"],
    "한익스프레스": ["Han Express", "한익스프레스", "#D35400"],
    
    # Fallback / Exception handling for "Others"
    "기타": ["Others", "기타", "#E0E0E0"],
}

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

def get_company_info(comp_name, lang='ko'):
    if comp_name in COMPANY_INFO:
        en_name, ko_name, color = COMPANY_INFO[comp_name]
        name = en_name if lang == "en" else ko_name
        return name, color
    else:
        # Fallback handling for companies not listed in the dictionary
        return comp_name, "#95A5A6"

# 3. Data Processing Function (기타(Others) 자동 계산 로직 적용)
def prepare_stacked_data(df_ratio, df_total):
    processed_records = []
    years = sorted(df_ratio["YEAR"].unique())

    for yr in years:
        threshold = 10

        # 해당 연도의 전체 등록 건수 가져오기
        tot_sub = df_total[df_total["YEAR"] == yr]
        total_cnt = tot_sub["REGISTRATION_COUNT"].values[0] if not tot_sub.empty else 0

        # 해당 연도의 상위 기업들 추출 (내림차순 정렬)
        top5 = df_ratio[df_ratio["YEAR"] == yr].sort_values(
            by="REGISTRATION_COUNT", ascending=False
        )
        top5_filtered = top5[top5["REGISTRATION_COUNT"] >= threshold]
        top5_sum = 0

        # 상위 1~5위 기업 데이터 생성
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

        # 📌 핵심 수정: 전체 건수에서 Top 5 합을 빼서 'Others' 건수를 구함
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

        # 'Others' 영역 높이를 15%로 축소 스케일링
        OTHERS_SCALE = 0.15

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
                    name, color = get_company_info(comp, lang=lang)
                    h = cnt * OTHERS_SCALE if cat == "Others" else cnt
                    plot_heights.append(h)
                    segment_colors.append(color)
                    labels.append((name, cnt, ratio))
                else:
                    plot_heights.append(0)
                    segment_colors.append('#E0E0E0')
                    labels.append(("", 0, 0.0))

            plot_heights = np.array(plot_heights)

            # Stacked Bar 그리기
            bars = ax.bar(
                [f"{yr}yr" if lang == "en" else f"{yr}년" for yr in years],
                plot_heights,
                bottom=bottoms,
                color=segment_colors,
                width=0.55,
                edgecolor="white",
                linewidth=0.8,
            )

            # 막대 내부 텍스트 라벨 추가
            for b_idx, (bar, (comp_name, real_cnt, ratio_val)) in enumerate(
                zip(bars, labels)
            ):
                if real_cnt > 0:
                    y_pos = bottoms[b_idx] + (plot_heights[b_idx] / 2.0)

                    if idx < 5:  # Top 1~5 기업 라벨
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
                            linespacing=0.9,
                        )
                    else:  # 'Others' 회색 막대 영역 라벨
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

        # 각 연도 막대 상단에 'Total: XXX' 표시
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

        # 차트 제목 및 주석 설정
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

        # extract top 5 companies from the chart data
        top_companies = df_stacked[df_stacked["CATEGORY"] != "Others"]["COMPANY_NAME"].unique()

        # create legend handles
        legend_handles = []
        for comp in top_companies:
            display_name, color = get_company_info(comp, lang=lang)
            # create patch object
            patch = mpatches.Patch(color=color, label=display_name)
            legend_handles.append(patch)
        # add 'Others' patch
        others_label = "Others" if lang == "en" else "기타"
        legend_handles.append(mpatches.Patch(color="#E0E0E0", label=others_label))

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