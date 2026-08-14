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

import platform
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

plt.rc("font", family="Malgun Gothic")  # Windows: Malgun Gothic / Mac: AppleGothic
plt.rc("axes", unicode_minus=False)

base_dir = Path(".")
data_dir = base_dir / "data/processed"
data_dir.mkdir(parents=True, exist_ok=True)
save_dir = base_dir / "output"

# # load data
file_path = data_dir / "tradedata_dj_2020_2025_rank_vs01_01.csv"
df = pd.read_csv(file_path)

# Plot Grouped Bar Chart
plt.figure(figsize=(12, 6))
ax = sns.barplot(
    data=df, x="year", y="sales_by_sectional", hue="section_name", palette="Set2"
)

plt.title(
    "연도별 주요 품목군 수출액 비교 (Grouped Bar Chart)",
    fontsize=15,
    pad=15,
    fontweight="bold",
)
plt.xlabel("연도 (Year)", fontsize=12)
plt.ylabel("수출액 (Sales Volume)", fontsize=12)
plt.gca().yaxis.set_major_formatter("{x:,.0f}")
plt.legend(title="품목군", bbox_to_anchor=(1.02, 1), loc="upper left")

plt.tight_layout()
plt.savefig(save_dir / "01_01_grouped_bar_chart.jpg", dpi=300)
