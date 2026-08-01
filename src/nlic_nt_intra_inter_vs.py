from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

# ----------------------------------------------------
# 1. Directory setup & Data load
# ----------------------------------------------------
base_dir = Path(".")
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)
data_dir = base_dir / "data"

# 데이터 로드
df = pd.read_csv(data_dir / "nlic_nt_freight_weight.csv")

# 폰트 설정 (Windows 기준)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# ----------------------------------------------------
# 2. I18N (다국어 라벨 설정)
# ----------------------------------------------------
I18N = {
    "ko": {
        "filename": "6_nt_intra_vs_inter_vs_ko.png",
        "title": "전국 총 물동량: 권역 내 vs 권역 간 이동 추이 (2019-2023)",
        "xlabel": "연도",
        "ylabel_left": "물동량 (억 톤)",
        "ylabel_right": "권역 내 비중 (%)",
        "label_intra": "전국 권역 내 이동 (Intra-region)",
        "label_inter": "전국 권역 간 이동 (Inter-region)",
        "label_ratio": "권역 내 비중 (%)",
        "year_suffix": "년",
        "unit": "억톤",
    },
    "en": {
        "filename": "6_nt_intra_vs_inter_vs_en.png",
        "title": "National Cargo Volume: Intra-region vs Inter-region Trend (2019-2023)",
        "xlabel": "Year",
        "ylabel_left": "Cargo Volume (100M Tons)",
        "ylabel_right": "Intra-region Ratio (%)",
        "label_intra": "Intra-region Flow",
        "label_inter": "Inter-region Flow",
        "label_ratio": "Intra-region Ratio (%)",
        "year_suffix": "yr",
        "unit": "100MT",
    },
}

# ----------------------------------------------------
# 3. 데이터 집계 및 가공
# ----------------------------------------------------
pivot_df = df.groupby(["연도", "logistics_type"])["물동량"].sum().unstack()

# 단위 변환 (톤 -> 억 톤)
pivot_df["권역 내_억톤"] = pivot_df["권역 내"] / 1e8
pivot_df["권역 간_억톤"] = pivot_df["권역 간"] / 1e8

# 권역 내 물동량 비중(%) 계산
pivot_df["전체물동량"] = pivot_df["권역 내"] + pivot_df["권역 간"]
pivot_df["권역내_비율"] = (pivot_df["권역 내"] / pivot_df["전체물동량"]) * 100


# ----------------------------------------------------
# 4. Plotting Function (국/영문 그래프 저장 루프)
# ----------------------------------------------------
def generate_summary_plots():
    for lang, cfg in I18N.items():
        fig, ax1 = plt.subplots(figsize=(10, 6))

        years = [f'{y}{cfg["year_suffix"]}' for y in pivot_df.index]
        x = range(len(years))
        bar_width = 0.35

        # [왼쪽 Y축] 막대 그래프 (물동량)
        rects1 = ax1.bar(
            [i - bar_width / 2 for i in x],
            pivot_df["권역 내_억톤"],
            bar_width,
            label=cfg["label_intra"],
            color="#2B5C8F",
        )
        rects2 = ax1.bar(
            [i + bar_width / 2 for i in x],
            pivot_df["권역 간_억톤"],
            bar_width,
            label=cfg["label_inter"],
            color="#76B7B2",
        )

        ax1.set_ylabel(cfg["ylabel_left"], fontsize=12, fontweight="bold", labelpad=10)
        ax1.set_xlabel(cfg["xlabel"], fontsize=12, fontweight="bold", labelpad=10)
        ax1.set_xticks(x)
        ax1.set_xticklabels(years, fontsize=11)
        ax1.set_ylim(0, 16)
        ax1.grid(axis="y", linestyle="--", alpha=0.5)

        # 막대 위 수치 데이터 표시
        for rect in rects1:
            h = rect.get_height()
            ax1.annotate(
                f'{h:.2f}{cfg["unit"]}',
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
            )

        for rect in rects2:
            h = rect.get_height()
            ax1.annotate(
                f'{h:.2f}{cfg["unit"]}',
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
            )

        # [오른쪽 Y축] 꺾은선 그래프 (권역 내 비중 %)
        ax2 = ax1.twinx()
        line = ax2.plot(
            x,
            pivot_df["권역내_비율"],
            color="#E15759",
            marker="o",
            linewidth=2.5,
            label=cfg["label_ratio"],
        )
        ax2.set_ylabel(
            cfg["ylabel_right"],
            fontsize=12,
            fontweight="bold",
            color="#E15759",
            labelpad=10,
        )
        ax2.set_ylim(40, 80)
        ax2.tick_params(axis="y", labelcolor="#E15759")

        # 꺾은선 위 비중(%) 표시
        for i, txt in enumerate(pivot_df["권역내_비율"]):
            ax2.annotate(
                f"{txt:.1f}%",
                (i, txt),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                fontweight="bold",
                color="#B03A2E",
            )

        # 범례 통합
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=True)

        plt.title(cfg["title"], fontsize=14, fontweight="bold", pad=15)
        plt.tight_layout()

        # 지정된 경로(NLIC/output)에 이미지 저장
        output_file = save_dir / cfg["filename"]
        plt.savefig(output_file, dpi=300)
        plt.close()
        print(f"Saved plot to: {output_file.resolve()}")


# 실행
generate_summary_plots()
