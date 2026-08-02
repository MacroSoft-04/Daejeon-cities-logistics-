import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import platform
from pathlib import Path

# 1. 한글 폰트 설정 (OS별 자동 적용)
if platform.system() == "Windows":
    plt.rc("font", family="Malgun Gothic")
elif platform.system() == "Darwin":  # Mac OS
    plt.rc("font", family="AppleGothic")
else:  # Linux
    plt.rc("font", family="NanumGothic")

plt.rcParams["axes.unicode_minus"] = False

# 경로 설정
base_dir = Path(".")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 2. 데이터 불러오기
file_path = data_dir / "nlictr_commodity_cat.csv"
df = pd.read_csv(file_path)

# 3. 데이터 전처리 ('반입', '반출' 구분 데이터 추출 및 만 톤 단위 변환)
df_io = df[
    (df["구분"].isin(["반입", "반출"]))
    & (df["region_kr"].isin(["충청권(대전제외)", "대전시", "수도권"]))
].copy()

df_io["물동량_만톤"] = df_io["물동량_톤"] / 10000

# 피벗 테이블 생성 (지역 x 연도 x 반입/반출 x 품목 카테고리)
piv_all = df_io.pivot_table(
    index=["region_kr", "연도", "구분"],
    columns="commodity_cat_kr",
    values="물동량_만톤",
    aggfunc="sum",
).fillna(0)

# 4. 시각화 설정 (Butterfly 차트)
years = [2019, 2020, 2021, 2022, 2023]
categories = [
    "기타 화물",
    "농축수산물 및 신선식품",
    "소비재 및 이커머스",
    "재생재료",
    "제조업 및 장비",
    "중화학 및 원자재",
]
colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc949"]

fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(24, 7), sharey=True)
regions = ["충청권(대전제외)", "대전시", "수도권"]

for i, reg in enumerate(regions):
    ax = axes[i]
    y_pos = np.arange(len(years))
    bar_height = 0.5
    df_reg = piv_all.loc[reg]

    # [Left: 반출 (Export)] - 음수 처리하여 왼쪽으로 스택
    left_stack = np.zeros(len(years))
    for c_idx, cat in enumerate(categories):
        vals_out = [
            df_reg.loc[(y, "반출"), cat] if (y, "반출") in df_reg.index else 0
            for y in years
        ]
        vals_out_neg = [-v for v in vals_out]
        ax.barh(
            y_pos,
            vals_out_neg,
            height=bar_height,
            left=left_stack,
            label=cat if i == 0 else "",
            color=colors[c_idx],
            edgecolor="white",
            linewidth=0.5,
            alpha=0.9,
        )
        left_stack += vals_out_neg

    # [Right: 반입 (Import)] - 양수 그대로 오른쪽으로 스택
    right_stack = np.zeros(len(years))
    for c_idx, cat in enumerate(categories):
        vals_in = [
            df_reg.loc[(y, "반입"), cat] if (y, "반입") in df_reg.index else 0
            for y in years
        ]
        ax.barh(
            y_pos,
            vals_in,
            height=bar_height,
            left=right_stack,
            color=colors[c_idx],
            edgecolor="white",
            linewidth=0.5,
        )
        right_stack += vals_in

    # Y축 및 X축 라벨 세팅
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{y}년" for y in years], fontsize=11, fontweight="bold")
    ax.axvline(0, color="black", linewidth=1.2)  # 중앙 0 분리선
    ax.set_title(
        f"[{reg}] 반출(◀ Left) vs 반입(Right ▶) 물동량 비교 (2019~2023)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("◀ 반출 물동량 (만 톤)  |  반입 물동량 (만 톤) ▶", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    # X축 눈금 음수를 절댓값(양수)으로 변환
    ticks = ax.get_xticks()
    ax.set_xticklabels([f"{abs(int(t)):,}" for t in ticks])

# 공통 범례 설정
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    title="품목 카테고리",
    bbox_to_anchor=(1.01, 0.85),
    loc="upper left",
    fontsize=10,
)

plt.tight_layout()

# 이미지 저장 경로 지정 (save_dir 활용)
output_path = save_dir / "11_chung_dj_cp_cat.jpg"
plt.savefig(output_path, dpi=300, bbox_inches="tight")

print(f"그래프가 '{output_path}'에 저장되었습니다.")
