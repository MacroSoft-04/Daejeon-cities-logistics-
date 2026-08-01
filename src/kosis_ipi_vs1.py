import os
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

base_dir = Path(".")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)
save_dir = base_dir / "output"
# 2. 데이터 불러오기
file_path = data_dir / "kosis_ipi_clean2.csv"
df = pd.read_csv(file_path)
# -------------------------------------------------------------
# 1. 한글 폰트 및 마이너스 기호 깨짐 방지 설정
# -------------------------------------------------------------
plt.rc("font", family="Malgun Gothic")  # Windows: Malgun Gothic / Mac: AppleGothic
plt.rc("axes", unicode_minus=False)

# -------------------------------------------------------------
# 2. SQL 결과 CSV 파일 불러오기
# -------------------------------------------------------------

# 날짜 컬럼을 datetime 타입으로 변환
df["날짜"] = pd.to_datetime(df["날짜"])

# -------------------------------------------------------------
# 3. 그래프 스타일 및 색상(Palette) 설정
# -------------------------------------------------------------
# 대전만 강렬한 빨간색으로 강조하고, 나머지 권역은 대비되는 색상으로 배치
custom_palette = {
    "대전": "#E60012",  # 메인 타깃 (강렬한 Red)
    "충청권": "#0055B8",  # 인접 권역 (Deep Blue)
    "수도권": "#555555",  # 주요 권역 (Dark Gray)
    "영남권": "#AAAAAA",  # 타 권역 (Medium Gray)
    "호남권": "#CCCCCC",  # 타 권역 (Light Gray)
    "기타": "#DDDDDD",  # 기타 (Very Light Gray)
}

# 대전 선을 맨 위에 그리기 위해 데이터 순서 정렬
region_order = ["기타", "호남권", "영남권", "수도권", "충청권", "대전"]
df["region"] = pd.Categorical(df["region"], categories=region_order, ordered=True)
df = df.sort_values(by=["날짜", "region"])

# -------------------------------------------------------------
# 4. 시각화 그리기
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7), dpi=300)

# Seaborn Lineplot
sns.lineplot(
    data=df,
    x="날짜",
    y="avg_index",
    hue="region",
    palette=custom_palette,
    linewidth=1.8,
    ax=ax,
)

# '대전' 선만 두껍게 강조 (Line Width 3.0)
for line in ax.lines:
    if line.get_label() == "대전":
        line.set_linewidth(3.2)
        line.set_zorder(10)  # 맨 앞으로 끌어올림

# 기준선 100 표시 (2020년 기준점)
ax.axhline(
    100, color="black", linestyle="--", linewidth=1.2, alpha=0.7, label="기준선 (100)"
)

# -------------------------------------------------------------
# 5. 차트 디테일 설정 (타이틀, 축, 범례)
# -------------------------------------------------------------
ax.set_title(
    "대전 vs 주요 권역별 광공업 출하 총지수 추이 (2018 ~ 2026)",
    fontsize=16,
    fontweight="bold",
    pad=20,
)
ax.set_xlabel("연도 (Year)", fontsize=12, labelpad=10)
ax.set_ylabel("계절조정 출하지수 (2020=100)", fontsize=12, labelpad=10)

# X축 연도 범주 가독성 개선
ax.grid(True, linestyle=":", alpha=0.6)
ax.set_ylim(df["avg_index"].min() - 5, df["avg_index"].max() + 5)

# 범례(Legend) 설정: 대전이 맨 위에 오도록 순서 조정 및 차트 밖에 위치
handles, labels = ax.get_legend_handles_labels()
# 대전과 기준선을 상단에 강조 배치
ax.legend(
    handles=handles[::-1],
    labels=labels[::-1],
    title="권역 구분",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    frameon=True,
    fontsize=11,
)

plt.tight_layout()

# -------------------------------------------------------------
# 6. 고해상도 이미지 저장
# -------------------------------------------------------------
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
save_path = output_dir / "dj_ipi_mth_trend.jpg"

plt.savefig(save_path, dpi=300, bbox_inches="tight")
print(f"✅ 그래프가 성공적으로 저장되었습니다: {save_path}")

plt.show()
