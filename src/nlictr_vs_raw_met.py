from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 한글 폰트 및 마이너스 깨짐 설정
plt.rc("font", family="Malgun Gothic")  # Windows: Malgun Gothic / Mac: AppleGothic
plt.rc("axes", unicode_minus=False)

base_dir = Path(".")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 1. 데이터 불러오기 (행 구조로 변경된 데이터)
top5_df = pd.read_csv(data_dir / "nlictr_raw_meterial_detail.csv")

# 2. 물동량 단위 조정 (천 톤 단위)
df_21_22_gap = top5_df[top5_df["year"] == 2022].copy()

# 2. 증감량 단위 조정 (천 톤)
df_21_22_gap["gap_vol_k"] = df_21_22_gap["gap_from_prev_year"] / 1000

# 3. Y축 라벨 생성 (히트맵과 비슷하게)
df_21_22_gap["y_label"] = (
    "["
    + df_21_22_gap["rank_num"].astype(str)
    + "위]\n"
    + df_21_22_gap["flow_type"]
    + "\n("
    + df_21_22_gap["commodity"]
    + ")"
)
g = sns.FacetGrid(
    df_21_22_gap,
    row="region_kr",
    sharex=False,  # 💡 중요: 각 권역별로 X축(변동폭) 스케일 독립 설정
    height=3,
    aspect=3.5,
    palette="RdBu",  # 양수/음수를 잘 구분하는 팔레트
)

# 막대 차트 그리기
g.map(sns.barplot, "gap_vol_k", "y_label", orient="h")

# 데이터 값 표시 및 스타일 설정
for i, (ax_row_label, ax) in enumerate(g.axes_dict.items()):
    region_data = df_21_22_gap[df_21_22_gap["region_kr"] == ax_row_label]

    # 각 막대에 데이터 값 표시 (± 부호 포함)
    for index, value in enumerate(region_data["gap_vol_k"]):
        label = f"{value:+,.0f} 천 톤"
        # X축 스케일에 맞춰 텍스트 위치 동적 조정
        xlim = ax.get_xlim()
        x_pos = value * 1.05 if value > 0 else value - (xlim[1] - xlim[0]) * 0.15

        ax.text(
            x_pos,
            index,
            label,
            color="black",
            ha="left" if value > 0 else "right",
            va="center",
            fontweight="bold",
            fontsize=9,
        )

    # 0 기준선 추가
    ax.axvline(0, color="black", linestyle="-", linewidth=1)

    # 스타일 세팅
    ax.set_title(
        f"{ax_row_label} (21-22년 변동폭)", fontsize=11, fontweight="bold", pad=10
    )
    ax.set_xlabel("변동량 (천 톤, ±)", fontsize=10)
    ax.set_ylabel("", fontsize=10)  # 품목 정보가 이미 Label에 있음
    ax.grid(axis="x", linestyle="--", alpha=0.5)

# 전체 타이틀 추가
plt.subplots_adjust(top=0.92)
g.fig.suptitle(
    "2021~2022년 변동폭 Top 2 품목 (권역별 독립 스케일)", fontsize=14, fontweight="bold"
)

# 5. 저장 및 출력
plt.tight_layout(rect=[0, 0, 1, 0.98])

# 6. 저장
save_path = save_dir / "13_raw_materials_detail.jpg"
plt.savefig(save_path, dpi=300, bbox_inches="tight")
