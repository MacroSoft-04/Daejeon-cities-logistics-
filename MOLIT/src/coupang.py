import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 1. Path Settings
base_dir = Path(".")
data_dir = base_dir / "MOLIT" / "data"
save_dir = base_dir / "MOLIT" / "output"
save_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(data_dir / "coupang.csv")

# 2. 행정구역(SIDO)을 5대 주요 권역으로 매핑하는 함수 정의
def map_region(sido):
    if sido in ['서울특별시', '경기도', '인천광역시']:
        return '수도권'
    elif sido in ['대전광역시', '세종특별자치시', '충청남도', '충청북도']:
        return '충청권'
    elif sido in ['부산광역시', '대구광역시', '울산광역시', '경상남도', '경상북도']:
        return '영남권'
    elif sido in ['전북특별자치도', '전남광주통합특별시', '전라남도', '전라북도', '광주광역시']:
        return '호남권'
    else:
        return '기타 (강원/제주 등)'

df['REGION'] = df['SIDO'].apply(map_region)

# 3. 연도(2019~2025) 및 권역별 등록 건수 피벗 테이블 생성
df_pivot = df.pivot_table(index='YEAR', columns='REGION', values='REGISTRATION_COUNT', aggfunc='sum').fillna(0)

# 모든 연도(2019~2025)가 포함되도록 인덱스 재설정
all_years = list(range(2019, 2026))
df_pivot = df_pivot.reindex(all_years, fill_value=0)

# 권역 출력 순서 및 팔레트 컬러 설정
region_order = ['수도권', '영남권', '호남권', '충청권', '기타 (강원/제주 등)']
df_plot = df_pivot[region_order]
colors = ['#2980B9', '#E67E22', '#2ECC71', '#E74C3C', '#95A5A6'] # 수도권(파랑), 영남(주황), 호남(초록), 충청(빨강), 기타(회색)

# 4. 한글 폰트 설정 (Windows 기준 'Malgun Gothic', Mac은 'AppleGothic')
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 5. 차트 그리기
fig, ax = plt.subplots(figsize=(12, 7))

bottoms = np.zeros(len(df_plot))

for idx, col in enumerate(df_plot.columns):
    values = df_plot[col].values
    bars = ax.bar(
        [f"{yr}년" for yr in df_plot.index],
        values,
        bottom=bottoms,
        label=col,
        color=colors[idx],
        width=0.55,
        edgecolor="white",
        linewidth=1
    )
    
    # 막대 내부 세부 수치 라벨링 (2건 이상일 때만 수치 표시)
    for b_idx, (bar, val) in enumerate(zip(bars, values)):
        if val >= 2:
            y_pos = bottoms[b_idx] + val / 2.0
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{int(val)}",
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color="white"
            )
            
    bottoms += values

# 막대 상단에 연도별 총 합계 표시
for idx, tot in enumerate(bottoms):
    if tot > 0:
        ax.text(
            idx,
            tot + 1.5,
            f"총 {int(tot)}건",
            ha="center",
            va="bottom",
            fontsize=10.5,
            fontweight="bold",
            color="#222222"
        )

# 6. 차트 제목 및 서브 타이틀(핵심 메시지) 추가
ax.set_title("권역별 풀필먼트/로지스틱스(FC) 거점 신설 추이 (2019~2025)", fontsize=15, pad=20, fontweight="bold")
ax.set_xlabel("연도", fontsize=11, labelpad=10)
ax.set_ylabel("신규 거점 등록 건수", fontsize=11, labelpad=10)
ax.set_ylim(0, max(bottoms) * 1.12)

# 핵심 메시지 코멘트 추가
ax.text(
    0.01, 0.96,
    "* 2021년 이후 수도권, 영남권, 호남권 등 대전 외곽 권역에 자체 FC 거점이 폭발적으로 증가함",
    transform=ax.transAxes,
    fontsize=10,
    color="#D35400",
    fontweight="bold"
)

# 그리드 및 범례 설정
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)
ax.legend(title="권역 구분", loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True)

plt.tight_layout()
plt.show()