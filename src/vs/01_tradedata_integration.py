"""
====================================================================
* Author: Minseo Kim
* Data Sources:
    - 수출입 무역통계/지역별 실적_대전광역시(2020~2025)
    - tradedata/regional performance_Deajeon
    - https://tradedata.go.kr/cts/index.do
* visualizaiton:
    - Grouped Bar Chart(Yearly Top 5 sections by sales volume)
* Output: output/01_01_grouped_bar_chart.jpg
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
file_path = data_dir / "tradedata_dj_2020_2025.csv"
df = pd.read_csv(file_path)

df_grouped = df.groupby(["year", "section_name"], as_index=False).agg(
    {"export_usd": "sum", "import_usd": "sum"}
)

top5_ex_sections = (
    df_grouped.groupby("section_name")["export_usd"].sum().nlargest(5).index
)
top5_im_sections = (
    df_grouped.groupby("section_name")["import_usd"].sum().nlargest(5).index
)

df_ex_top5 = df_grouped[df_grouped["section_name"].isin(top5_ex_sections)]
df_im_top5 = df_grouped[df_grouped["section_name"].isin(top5_im_sections)]

# Plot Grouped Bar Chart
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
sns.lineplot(
    data=df_ex_top5,
    x="year",
    y="export_usd",
    hue="section_name",
    marker="o",
    linewidth=2.5,
    ax=ax1,
    palette="tab10",
)

ax1.set_title(
    "연도별 주요 품목군 수출액 비교 (top5)",
    fontsize=15,
    pad=15,
    fontweight="bold",
)
ax1.set_xlabel("연도", fontsize=12)
ax1.set_ylabel("수출액 (천 달러)", fontsize=11)
ax1.yaxis.set_major_formatter("{x:,.0f}")
ax1.grid(True, linestyle="--", alpha=0.3, axis="y")
ax1.legend(title="품목군", bbox_to_anchor=(1.02, 1), loc="upper left")

sns.lineplot(
    data=df_im_top5,
    x="year",
    y="import_usd",
    hue="section_name",
    marker="o",
    linewidth=2.5,
    ax=ax2,
    palette="tab10",
)

ax2.set_title(
    "연도별 주요 품목군 수입액 비교 (top5)",
    fontsize=15,
    pad=15,
    fontweight="bold",
)
ax2.set_xlabel("연도", fontsize=12)
ax2.set_ylabel("수입액 (천 달러)", fontsize=11)
ax2.yaxis.set_major_formatter("{x:,.0f}")
ax2.grid(True, linestyle="--", alpha=0.3, axis="y")
ax2.legend(title="품목군", bbox_to_anchor=(1.02, 1), loc="upper left")

plt.tight_layout()
plt.savefig(save_dir / "01_grouped_bar_chart.jpg", dpi=300)
