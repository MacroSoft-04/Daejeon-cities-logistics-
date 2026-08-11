"""
====================================================================
* Author: Minseo Kim
* Data Sources:
    - 수출입 무역통계/지역별 실적_대전광역시(2020~2025)
    - tradedata/regional performance_Deajeon
    - https://tradedata.go.kr/cts/index.do
* visualizaiton:
    - Grouped Bar Chart(Yearly Top 5 sections by sales volume)
* Output: output/08_01_grouped_bar_chart.jpg
====================================================================
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 한글 폰트 설정
plt.rc("font", family="Malgun Gothic")
plt.rc("axes", unicode_minus=False)

# 데이터 로드
base_dir = Path(".")
data_dir = base_dir / "data"
save_dir = base_dir / "output"

df = pd.read_csv(data_dir / "tradedata_dj_2020_2025_rank_vs08.csv")

# 1. 데이터 피벗
pivot_df = df.pivot(
    index="year", columns="section_name", values="sales_by_sectional"
).fillna(0)

# 2. 핵심 카테고리만 재편성: [기계 및 전기기기, 수송기기, 기타]
pivot_grouped = pd.DataFrame(index=pivot_df.index)
pivot_grouped["기계 및 전기기기"] = pivot_df["기계 및 전기기기"]
pivot_grouped["수송기기"] = pivot_df["수송기기"]

# 나머지 품목들은 모두 '기타'로 합산
other_cols = [c for c in pivot_df.columns if c not in ["기계 및 전기기기", "수송기기"]]
pivot_grouped["기타"] = pivot_df[other_cols].sum(axis=1)

# 컬럼 순서 고정 (기계 -> 수송 -> 기타)
pivot_grouped = pivot_grouped[["기계 및 전기기기", "수송기기", "기타"]]

# 3. Subplot 구성 (위: 누적 막대, 아래: 수송기기 단독 꺾은선)
fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(10, 8),
    sharex=True,
    gridspec_kw={"height_ratios": [1.2, 1]},
)

# -------------------------------------------------------------------
# [상단 차트] 전체 수출 구조 (누적 막대그래프)
# -------------------------------------------------------------------
years = pivot_grouped.index.astype(str)
width = 0.55
colors = ["#2b5c8f", "#e74c3c", "#bdc3c7"]  # 파랑(기계), 빨강(수송), 회색(기타)
texts = []

bottom = np.zeros(len(years))
for col, color in zip(pivot_grouped.columns, colors):
    values = pivot_grouped[col].values
    ax1.bar(
        years,
        values,
        bottom=bottom,
        label=col,
        color=color,
        width=width,
        edgecolor="white",
    )
    bottom += values

ax1.set_title(
    "대전시 주요 품목별 수출 구조 및 수송기기 성장 추이",
    fontsize=14,
    fontweight="bold",
    pad=15,
)
ax1.set_ylabel("총 수출액", fontsize=11)
ax1.yaxis.set_major_formatter("{x:,.0f}")
ax1.grid(True, linestyle="--", alpha=0.3, axis="y")
ax1.legend(bbox_to_anchor=(1.02, 1), loc="upper left", title="품목 구분")

# -------------------------------------------------------------------
# [하단 차트] '수송기기' 단독 꺾은선 그래프 (확대)
# -------------------------------------------------------------------
transport_vals = pivot_grouped["수송기기"].values

ax2.plot(
    years,
    transport_vals,
    marker="o",
    color="#e74c3c",
    linewidth=2.8,
    markersize=7,
    label="수송기기 (핵심 성장 품목)",
)
ax2.fill_between(
    years, transport_vals, color="#e74c3c", alpha=0.08
)  # 은은한 하단 색상 채우기

ax2.set_xlabel("연도 (Year)", fontsize=11, fontweight="bold")
ax2.set_ylabel("수출액 (수송기기 확대)", fontsize=11)
ax2.yaxis.set_major_formatter("{x:,.0f}")
ax2.grid(True, linestyle="--", alpha=0.5)

# 수치 텍스트 및 증감율 표기
v2020 = pivot_grouped.loc[2020, "수송기기"]
v2025 = pivot_grouped.loc[2025, "수송기기"]
pct_growth = ((v2025 - v2020) / v2020) * 100

for i, v in enumerate(transport_vals):
    ax2.text(
        i,
        v + 15000,
        f"{v:,.0f}",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color="#2c3e50",
    )

ax2.annotate(
    f"{pct_growth:.1f}% 증가 ▲ (2020 대비)",
    xy=(len(years) - 1, v2025),
    xytext=(len(years) - 2.2, v2025 + 25000),
    fontweight="bold",
    color="#e74c3c",
    fontsize=10,
    arrowprops=dict(arrowstyle="->", color="#e74c3c", lw=1.5),
)

ax2.set_ylim(300000, 820000)
ax2.legend(loc="upper left")

plt.tight_layout()

# 저장
save_path = save_dir / "08_stacked_and_transport_focus.jpg"
plt.savefig(save_path, dpi=300, bbox_inches="tight")
