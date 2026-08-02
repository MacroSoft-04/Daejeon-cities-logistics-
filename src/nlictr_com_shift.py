from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 한글 폰트 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

base_dir = Path(".")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 1. SQL 추출 결과 데이터 불러오기
df_raw = pd.read_csv(data_dir / "nlictr_flow_shift.csv")

# 2. '원자재 및 기초소재' 품목만 필터링
df_mat = df_raw[df_raw["commodity_category"] == "원자재 및 기초소재"].copy()

# 3. Wide-form -> Long-form 변환
df_long = pd.melt(
    df_mat,
    id_vars=["region_kr", "flow_type", "commodity_category"],
    value_vars=["vol_2020", "vol_2021", "vol_2022", "vol_2023"],
    var_name="year_str",
    value_name="cargo_volume",
)

df_long["year"] = df_long["year_str"].str.replace("vol_", "").astype(int)

# -------------------------------------------------------------
# 🔥 [핵심] 2020년 = 100 기준 지수화(Indexation) 계산
# -------------------------------------------------------------
# 연도 기준 정렬 후 그룹별 첫 번째 값(2020년)으로 나누고 100을 곱함
df_long = df_long.sort_values(by=["region_kr", "flow_type", "year"])
df_long["index_val"] = df_long.groupby(["region_kr", "flow_type"])[
    "cargo_volume"
].transform(lambda x: (x / x.iloc[0]) * 100.0)


# 4. 권역별 지정 색상 설정
region_colors = {
    "대전시": "#E63946",  # 대전 강조 (Red)
    "충청권(대전제외)": "#1D3557",  # 충청권 (Blue)
    "수도권": "#8D99AE",  # 수도권 (Grey)
}

flow_types = ["반입", "반출"]

# 1행 2열 서브플롯 생성
fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(16, 7), sharey=True)

for idx, flow in enumerate(flow_types):
    ax = axes[idx]
    sub_df = df_long[df_long["flow_type"] == flow]

    for reg in ["수도권", "충청권(대전제외)", "대전시"]:
        reg_df = sub_df[sub_df["region_kr"] == reg]

        ax.plot(
            reg_df["year"],
            reg_df["index_val"],  # 지수화 데이터 Plotting
            marker="o",
            markersize=6,
            linewidth=2.0,
            color=region_colors[reg],
            label=reg,
        )

    # 100 기준선(Base Line) 표시
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)

    # 서브플롯 스타일
    ax.set_title(
        f"[원자재 및 기초소재] {flow} 물동량 지수 추이 (2020년=100)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("연도", fontsize=11)
    ax.set_ylabel("물동량 지수 (2020=100)" if idx == 0 else "", fontsize=11)
    ax.set_xticks([2020, 2021, 2022, 2023])
    ax.grid(True, linestyle=":", alpha=0.6)

# -------------------------------------------------------------
# 단일 외부 범례 우측 바깥 배치
# -------------------------------------------------------------
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    title="권역",
    loc="center left",
    bbox_to_anchor=(0.89, 0.5),
    frameon=True,
    fontsize=10,
    title_fontsize=11,
)

fig.suptitle(
    "원자재 및 기초소재 권역별 상대적 물동량 변동 흐름 (2020-2023 지수화)",
    fontsize=16,
    fontweight="bold",
    y=0.98,
)

plt.tight_layout(rect=[0, 0.03, 0.90, 0.95])

# 2020년과 2023년 원자재 반출 톤수 비교 (예시)
raw_2020 = df_long[
    (df_long["year"] == 2020)
    & (df_long["commodity_category"] == "원자재 및 기초소재")
    & (df_long["flow_type"] == "반출")
]
raw_2023 = df_long[
    (df_long["year"] == 2023)
    & (df_long["commodity_category"] == "원자재 및 기초소재")
    & (df_long["flow_type"] == "반출")
]

dj_diff = (
    raw_2020[raw_2020["region_kr"] == "대전시"]["cargo_volume"].values[0]
    - raw_2023[raw_2023["region_kr"] == "대전시"]["cargo_volume"].values[0]
)
others_diff = (
    raw_2023[raw_2023["region_kr"] != "대전시"]["cargo_volume"].sum()
    - raw_2020[raw_2020["region_kr"] != "대전시"]["cargo_volume"].sum()
)

summary_text = (
    f"2020년 대비 2023년 원자재 반출량 변동 비교\n"
    f"• 대전시 반출 감소량:  -{dj_diff/10000:.1f}만 톤 (대전 공급망 급감)\n"
    f"• 타 권역(수도권+충청권) 증가량: +{others_diff/10000:.1f}만 톤 (타 지역 반출 확장)"
)

# 하단에 텍스트 박스 배치
fig.text(
    0.5,
    0.02,
    summary_text,
    ha="center",
    va="bottom",
    fontsize=11,
    fontweight="bold",
    bbox=dict(
        boxstyle="round,pad=0.8",
        facecolor="#F8F9FA",
        edgecolor="#E63946",
        linewidth=1.5,
    ),
)

# 텍스트 박스 공간 확보를 위해 rect 조절
plt.tight_layout(rect=[0, 0.12, 0.90, 0.95])

save_path = save_dir / "12_raw_materials_indexed_flow.jpg"
plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.close()
