import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

plt.rc("font", family="Malgun Gothic")  # Windows: Malgun Gothic / Mac: AppleGothic
plt.rc("axes", unicode_minus=False)

base_dir = Path(".")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)
save_dir = base_dir / "output"

# 2. 데이터 불러오기 및 전처리
df = pd.read_csv(data_dir / "nlictr_raw_meterial_detail.csv")

# 물동량 단위 정리 (천 톤 단위로 조정)
df["cargo_volume_k"] = df["cargo_volume"] / 1000

# 세부 품목(commodity) 목록 및 서브플롯용 지역 목록
commodities = df["commodity"].unique()
regions = ["충청권(대전제외)", "대전시", "수도권"]
years = sorted(df["year"].unique())

# 품목별 구분용 색상 맵 설정
colors = plt.cm.tab10(np.linspace(0, 1, len(commodities)))
color_dict = dict(zip(commodities, colors))

# 3. 서브플롯 생성 (3개 지역 비교)
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

for i, region in enumerate(regions):
    ax = axes[i]
    df_reg = df[df["region_kr"] == region]

    y_pos = np.arange(len(years))
    bar_height = 0.5

    # 누적 막대 위치 추적용 배열
    left_accum = np.zeros(len(years))  # 반출 (좌측 음수 방향)
    right_accum = np.zeros(len(years))  # 반입 (우측 양수 방향)

    for comm in commodities:
        comm_color = color_dict[comm]

        # 연도별 반출/반입량 집계
        out_vals = []
        in_vals = []
        for y in years:
            out_v = df_reg[
                (df_reg["year"] == y)
                & (df_reg["flow_type"] == "반출")
                & (df_reg["commodity"] == comm)
            ]["cargo_volume_k"].sum()
            in_v = df_reg[
                (df_reg["year"] == y)
                & (df_reg["flow_type"] == "반입")
                & (df_reg["commodity"] == comm)
            ]["cargo_volume_k"].sum()
            out_vals.append(out_v)
            in_vals.append(in_v)

        out_vals = np.array(out_vals)
        in_vals = np.array(in_vals)

        # 좌측: 반출 (음수 방향 누적)
        ax.barh(
            y_pos,
            -out_vals,
            height=bar_height,
            left=-left_accum - out_vals,
            color=comm_color,
            label=comm if i == 0 else "",
        )
        left_accum += out_vals

        # 우측: 반입 (양수 방향 누적)
        ax.barh(y_pos, in_vals, height=bar_height, left=right_accum, color=comm_color)
        right_accum += in_vals

    # 중앙 기준선 (0)
    ax.axvline(0, color="gray", linewidth=1.2)

    # 축 세팅
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{y}년" for y in years])
    ax.set_title(
        f"[{region}] 반출(◀ Left) vs 반입(Right ▶) 물동량 비교 (2019~2023)",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlabel("◀ 반출 물동량 (천 톤) | 반입 물동량 (천 톤) ▶")

    # X축 눈금 표기를 절대값(양수)으로 변환 및 천 단위 쉼표 표기
    ax.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f"{abs(int(x)):,}")
    )
    ax.grid(True, linestyle="--", alpha=0.5, axis="x")

# 4. 범례(Legend) 배치
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    title="품목 (commodity)",
    loc="center left",
    bbox_to_anchor=(0.98, 0.5),
)

plt.tight_layout(rect=[0, 0, 0.97, 1])

save_path = save_dir / "13_raw_materials_detail.jpg"
plt.savefig(save_path, dpi=300, bbox_inches="tight")
