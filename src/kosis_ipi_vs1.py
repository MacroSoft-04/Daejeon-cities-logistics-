import os
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# -------------------------------------------------------------
# 1. 파일 경로 및 데이터 불러오기
# -------------------------------------------------------------
base_dir = Path(".")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

file_path = data_dir / "kosis_ipi_clean2.csv"
df = pd.read_csv(file_path)

# 날짜 컬럼 datetime 변환
df["date"] = pd.to_datetime(df["date"])

# -------------------------------------------------------------
# 2. 분석 대상 4개 권역 필터링 및 3개월 이동평균(Smooth) 처리
# -------------------------------------------------------------
target_regions = ["대전", "충청권", "수도권", "전국"]
df = df[df["region_kr"].isin(target_regions)].copy()

# ⭐️ 핵심: 뾰족뾰족한 월별 지그재그 노이즈를 줄이기 위한 3개월 이동평균 적용
df = df.sort_values(by=["region_kr", "date"])
df["smooth_index"] = df.groupby("region_kr")["avg_index"].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean()
)

# -------------------------------------------------------------
# 3. 한글 폰트 및 마이너스 기호 설정
# -------------------------------------------------------------
plt.rc("font", family="Malgun Gothic")  # Windows: Malgun Gothic / Mac: AppleGothic
plt.rc("axes", unicode_minus=False)

# -------------------------------------------------------------
# 4. 색상(Palette) 및 시각화 스타일 설정
# -------------------------------------------------------------
custom_palette = {
    "대전": "#E60013A4",  # 메인 타깃 (Red)
    "전국": "#222222",  # 비교 기준 (Dark Gray / 점선)
    "충청권": "#1B64B7A8",  # 인접 권역 (Deep Blue)
    "수도권": "#888888",  # 타 권역 (Medium Gray)
}

fig, ax = plt.subplots(figsize=(14, 7), dpi=300)

# -------------------------------------------------------------
# 5. 각 권역별 선 직접 그리기 (더 정밀한 두께 & zorder 제어)
# -------------------------------------------------------------
# 그리는 순서: 수도권 -> 충청권 -> 전국 -> 대전 (대전이 맨 위에 그려짐)
draw_order = ["수도권", "충청권", "전국", "대전"]

for region in draw_order:
    sub = df[df["region_kr"] == region]

    if region == "대전":
        ax.plot(
            sub["date"],
            sub["smooth_index"],
            color=custom_palette[region],
            linewidth=1.5,
            zorder=10,
            label="대전",
        )
    elif region == "전국":
        ax.plot(
            sub["date"],
            sub["smooth_index"],
            color=custom_palette[region],
            linewidth=2.0,
            linestyle="--",
            alpha=0.9,
            zorder=9,
            label="전국",
        )
    elif region == "충청권":
        ax.plot(
            sub["date"],
            sub["smooth_index"],
            color=custom_palette[region],
            linewidth=1.5,
            alpha=0.85,
            zorder=8,
            label="충청권",
        )
    else:  # 수도권
        ax.plot(
            sub["date"],
            sub["smooth_index"],
            color=custom_palette[region],
            linewidth=1.5,
            alpha=0.6,
            zorder=7,
            label="수도권",
        )

# -------------------------------------------------------------
# 6. 우측 끝 레이블 직접 표시 (Direct Labeling + 겹침 방지)
# -------------------------------------------------------------
last_date = df["date"].max()
last_data = df[df["date"] == last_date].sort_values(by="smooth_index")

# Y축 값이 너무 가깝지 않도록 텍스트 위치 최소 간격 유지 처리
prev_y = -999
for _, row in last_data.iterrows():
    region = row["region_kr"]
    val = row["smooth_index"]
    color = custom_palette.get(region, "#333333")

    # 텍스트 겹침 방지용 Y축 위치 조정 (최소 2.5pt 간격 확보)
    y_pos = max(val, prev_y + 2.5)
    prev_y = y_pos

    fontweight = "bold" if region in ["대전", "전국"] else "normal"
    fontsize = 11 if region in ["대전", "전국"] else 9.5

    ax.annotate(
        f" {region} ({val:.1f})",
        xy=(last_date, val),
        xytext=(last_date + pd.Timedelta(days=15), y_pos),
        fontsize=fontsize,
        fontweight=fontweight,
        color=color,
        va="center",
        ha="left",
    )

# 오른쪽 레이블 텍스트 여백 확보
x_max = last_date + pd.Timedelta(days=220)
ax.set_xlim(df["date"].min(), x_max)

# -------------------------------------------------------------
# 7. 디테일 스타일링 및 저장
# -------------------------------------------------------------
ax.set_title(
    "대전 vs 주요 권역 및 전국 광공업 출하 총지수 추이 (3개월 이동평균)",
    fontsize=15,
    fontweight="bold",
    pad=20,
)
ax.set_xlabel("연도 (Year)", fontsize=11, labelpad=10)
ax.set_ylabel("계절조정 출하지수 (2020=100)", fontsize=11, labelpad=10)
ax.grid(True, linestyle=":", alpha=0.5)

# 깔끔하게 우측 상단에 박스 범례도 함께 제공
ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True, facecolor="white")

plt.tight_layout()

# 고해상도 이미지 저장
save_path = save_dir / "9_dj_ipi_mth_trend.jpg"
plt.savefig(save_path, dpi=300, bbox_inches="tight")
print(f"✅ 수정된 그래프가 성공적으로 저장되었습니다: {save_path}")
