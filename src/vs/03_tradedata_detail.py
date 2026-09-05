"""
====================================================================
* Author: Minseo Kim
* Data: data/processed/tradedata_dj_2020_2025.csv (관세청 무역통계)
* Chart: the two commodities that move the trade balance, on one axis. Chart
  02 shows the balance turning negative in 2023; this shows which flows put
  it there, which the aggregate cannot say.
* Output: output/03_balance_drivers.jpg
====================================================================
"""

import matplotlib.pyplot as plt
import pandas as pd

from utils_chart import PALETTE, save, use_korean_font
from utils_validate_data import PROJECT_ROOT

SRC = PROJECT_ROOT / "data/processed/tradedata_dj_2020_2025.csv"
MILLION = 1_000  # source unit is thousand USD
SERIES = {
    "수송기기 수출": {
        "section": "수송기기",
        "value": "export_usd",
        "color": PALETTE["accent"],
    },
    "화학공업 제품 수입": {
        "section": "화학공업 제품",
        "value": "import_usd",
        "color": "#c8973f",
    },
}

use_korean_font()

df = pd.read_csv(SRC)
lines = {
    label: df[df["section_name"] == spec["section"]]
    .groupby("year")[spec["value"]]
    .sum()
    .sort_index()
    / MILLION
    for label, spec in SERIES.items()
}
years = next(iter(lines.values())).index.tolist()

fig, ax = plt.subplots(figsize=(10, 6))

for label, values in lines.items():
    color = SERIES[label]["color"]
    ax.plot(
        years, values, marker="o", markersize=7, linewidth=2.8, color=color, label=label
    )
    # The two lines cross twice; anchoring each label to the side its own line
    # sits on keeps them from landing on top of each other.
    others = [v for name, v in lines.items() if name != label]
    for year in years:
        value = values.loc[year]
        above = all(value >= other.loc[year] for other in others)
        ax.annotate(
            f"{value:,.0f}",
            xy=(year, value),
            xytext=(0, 11 if above else -17),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=color,
        )

# The deficit year is the reason this chart exists, so it is marked rather
# than left for the reader to locate.
balance = df.groupby("year")["balance"].sum()
ax.set_xticks(years)
ax.set_xlabel("연도")
ax.set_ylabel("금액 (백만 USD)")
ax.set_title(
    "수송기기 수출과 화학공업 제품 수입 추이",
    fontsize=15,
    fontweight="bold",
    pad=14,
)
ax.grid(True, axis="y", linestyle="--", alpha=0.35)
ax.legend(frameon=False, loc="upper left")
for side in ("top", "right"):
    ax.spines[side].set_visible(False)

low, high = ax.get_ylim()
ax.set_ylim(low, high + (high - low) * 0.12)

changes = " · ".join(
    f"{label} {(values.iloc[-1] / values.iloc[0] - 1) * 100:+.1f}%"
    for label, values in lines.items()
)
fig.text(
    0.5,
    -0.02,
    f"{years[0]}→{years[-1]} {changes} | 자료: 관세청 무역통계",
    ha="center",
    fontsize=9.5,
    color=PALETTE["text"],
)

save(fig, "03_balance_drivers.jpg")
