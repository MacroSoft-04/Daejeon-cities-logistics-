import os
import platform
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# 1. 한글 폰트 설정 (OS별 자동 적용)
if platform.system() == "Windows":
    plt.rc("font", family="Malgun Gothic")
elif platform.system() == "Darwin":  # Mac OS
    plt.rc("font", family="AppleGothic")
else:  # Linux
    plt.rc("font", family="NanumGothic")

plt.rcParams["axes.unicode_minus"] = False

base_dir = Path("./Seoul_household_logi")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)
save_dir = base_dir / "output"

# 2. 데이터 불러오기
file_path = data_dir / "seoul_cargo_flow.csv"
df = pd.read_csv(file_path)

# 3. 피벗 테이블로 변환 (그래프 그리기 좋은 형태)
# total_qty 피벗 (그래프 ①용)
pivot_qty = df.pivot(index="YEAR", columns="region_type", values="total_qty").fillna(0)
yearly_total = pivot_qty.sum(axis=1)

# ratio_pct 피벗 (그래프 ②용)
pivot_pct = df.pivot(index="YEAR", columns="region_type", values="ratio_pct").fillna(0)

# 4. 시각화 (2x1 서브플롯)
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 11))

# [그래프 1] 서울 유입 순수 외지 생활물류 총량 추이
years = pivot_pct.index.astype(str)
axes[0].plot(
    years,
    yearly_total.values / 10000,
    marker="o",
    linewidth=2.5,
    color="#1f77b4",
)
axes[0].set_title(
    "① 순수 서울 유입(O-S) 생활물류 총량 추이 (서울 내부 S-S 물량 제외)",
    fontsize=14,
    fontweight="bold",
    pad=12,
)
axes[0].set_ylabel("외지 유입 물동량 (만 건)", fontsize=11)
axes[0].grid(True, linestyle="--", alpha=0.5)

for i, txt in enumerate(yearly_total.values / 10000):
    axes[0].annotate(
        f"{txt:,.0f}만 건",
        (years[i], txt),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center",
        fontweight="bold",
    )

# [그래프 2] 권역별 출발 비중(%) 꺾은선 그래프 (이미 계산된 ratio_pct 컬럼 그대로 사용)
sudo_fc_pct = pivot_pct["수도권 외곽 (인천·경기)"]
etc_prov_pct = pivot_pct["기타 지방"]
dj_hub_pct = pivot_pct["대전"]

axes[1].plot(
    years,
    sudo_fc_pct,
    marker="s",
    linewidth=2.5,
    color="#2b5c8f",
    label="수도권 외곽 (인천·경기 FC)",
)
axes[1].plot(
    years,
    etc_prov_pct,
    marker="o",
    linewidth=2.5,
    color="#55a868",
    label="기타 지방 (부산·대구·충북 등)",
)
axes[1].plot(
    years,
    dj_hub_pct,
    marker="^",
    linewidth=2.5,
    color="#d62728",
    label="대전 (기존 중앙 HUB)",
)

axes[1].set_title(
    "② 서울 도착 물류 출발지 비중 추이: 인천·경기 FC 중심 고착화",
    fontsize=14,
    fontweight="bold",
    pad=12,
)
axes[1].set_ylabel("유입 비중 (%)", fontsize=11)
axes[1].set_xlabel("연도", fontsize=11)
axes[1].grid(True, linestyle="--", alpha=0.5)
axes[1].legend(loc="center right", fontsize=10, framealpha=0.9)

# 이미 완벽하게 계산되어 있던 ratio_pct 값 표시
for i in range(len(years)):
    axes[1].annotate(
        f"{sudo_fc_pct.iloc[i]:.1f}%",
        (years[i], sudo_fc_pct.iloc[i]),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center",
        color="#2b5c8f",
        fontweight="bold",
    )
    axes[1].annotate(
        f"{etc_prov_pct.iloc[i]:.1f}%",
        (years[i], etc_prov_pct.iloc[i]),
        textcoords="offset points",
        xytext=(0, 8),
        ha="center",
        color="#55a868",
        fontweight="bold",
    )
    axes[1].annotate(
        f"{dj_hub_pct.iloc[i]:.1f}%",
        (years[i], dj_hub_pct.iloc[i]),
        textcoords="offset points",
        xytext=(0, -15),
        ha="center",
        color="#d62728",
        fontweight="bold",
    )

axes[1].set_ylim(-2, 80)

plt.tight_layout()
plt.savefig(save_dir / "seoul_logistics_pure_os_line.jpg", dpi=300, bbox_inches="tight")
plt.show()
