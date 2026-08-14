"""
====================================================================
* Author: Minseo Kim
* Data Sources:
    - Trade Statistics / Regional Performance_Daejeon Metropolitan City (2020~2025)
    - https://tradedata.go.kr/cts/index.do
* Visualization:
    - Top: Stacked bar chart of exports by major commodity group
    - Bottom: Line chart focusing on Transport Equipment (zoomed)
* Output: output/08_stacked_and_transport_focus.jpg
====================================================================
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from adjustText import adjust_text

# Korean glyph support. Fallbacks: "AppleGothic" (macOS), "NanumGothic" (Linux)
plt.rc("font", family="Malgun Gothic")
plt.rc("axes", unicode_minus=False)

base_dir = Path(".")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(data_dir / "tradedata_dj_2020_2025_grouped_vs08.csv")

# Fixed panel order: the two growth-relevant groups first, residual last.
SECTION_ORDER = df["section_name"].unique()


def pivot_by_year(frame: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Reshape long-format trade records into year x section_name."""
    return frame.pivot(
        index="year", columns="section_name", values=value_col
    ).sort_index()[SECTION_ORDER]


sales_grouped = pivot_by_year(df, "sales_by_sectional")
ratio_grouped = pivot_by_year(df, "ratio")  # already stored as percent (0-100)

# extract the additional information for the "기타" section for the legend
other_rows = df[df["section_name"] == "기타"].sort_values("year")
if not other_rows.empty:
    latest_other = other_rows.iloc[-1]
    top_item = latest_other.get("other_top_section", "주요 품목")
    item_count = latest_other.get("other_section_count", 0)
    other_label_text = f"기타 ({top_item} 등 {int(item_count)}개 품목)"
else:
    other_label_text = "기타"

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(10, 8),
    sharex=True,
    gridspec_kw={"height_ratios": [1.2, 1]},
)

years = sales_grouped.index.astype(str)
x_pos = np.arange(len(years))
width = 0.55
colors = ["#2b5c8f", "#e74c3c", "#bdc3c7"]  # machinery / transport / other

other_cols = [c for c in sales_grouped.columns if c not in SECTION_ORDER]

# ---------------------------------------------------------------
# Top panel: overall export structure
# ---------------------------------------------------------------
texts = []
bottom = np.zeros(len(years))
# Two-line labels need more room than the single-line version did.
threshold = sales_grouped.sum(axis=1).max() * 0.05

for col, color in zip(SECTION_ORDER, colors):
    values = sales_grouped[col].to_numpy(dtype=float)
    shares = ratio_grouped[col].to_numpy(dtype=float)
    legend_label = other_label_text if col == "기타" else col
    ax1.bar(
        x_pos,
        values,
        bottom=bottom,
        label=legend_label,
        color=color,
        width=width,
        edgecolor="white",
    )

    for xi, (v, share, b) in enumerate(zip(values, shares, bottom)):
        # Segments below the threshold cannot fit a legible label.
        if v < threshold:
            continue
        texts.append(
            ax1.text(
                xi,
                b + v * 2 / 3,
                f"{share:.1f}%",
                ha="center",
                va="center",
                fontsize=8,
                linespacing=1.3,
                color="#2c3e50" if col == "기타" else "white",
            )
        )
    bottom += values

if texts:
    adjust_text(
        texts,
        ax=ax1,
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.5, alpha=0.7),
        only_move={"text": "y"},  # keep labels on their own bar; shift vertically only
    )

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

# ---------------------------------------------------------------
# Bottom panel: Transport Equipment on its own scale
# ---------------------------------------------------------------
transport_vals = sales_grouped["수송기기"].to_numpy(dtype=float)
transport_shares = ratio_grouped["수송기기"].to_numpy(dtype=float)

ax2.plot(
    x_pos,
    transport_vals,
    marker="o",
    color="#e74c3c",
    linewidth=2.8,
    markersize=7,
    label="수송기기 (핵심 성장 품목)",
)
ax2.fill_between(x_pos, transport_vals, color="#e74c3c", alpha=0.08)

ax2.set_xlabel("연도 (Year)", fontsize=11, fontweight="bold")
ax2.set_ylabel("수출액 (수송기기 확대)", fontsize=11)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(years)
ax2.yaxis.set_major_formatter("{x:,.0f}")
ax2.grid(True, linestyle="--", alpha=0.5)

# Derive the zoom window from the data so adding years never clips the line.
t_min, t_max = transport_vals.min(), transport_vals.max()
span = t_max - t_min if t_max > t_min else t_max * 0.2
ax2.set_ylim(t_min - span * 0.3, t_max + span * 0.45)

label_offset = span * 0.08
for xi, v in zip(x_pos, transport_vals):
    ax2.text(
        xi,
        v + label_offset,
        f"{v:,.0f}",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color="#2c3e50",
    )

# Endpoints come from the index, so the callout stays correct as the range grows.
first_year, last_year = sales_grouped.index[0], sales_grouped.index[-1]
v_first, v_last = transport_vals[0], transport_vals[-1]
pct_growth = ((v_last - v_first) / v_first) * 100 if v_first else np.nan
share_first, share_last = transport_shares[0], transport_shares[-1]

ax2.annotate(
    f"{pct_growth:.1f}% 증가 ▲ ({first_year} 대비)\n"
    f"비중 {share_first:.1f}% → {share_last:.1f}%",
    xy=(len(years) - 1, v_last),
    xytext=(len(years) - 2.2, v_last + span * 0.25),
    fontweight="bold",
    color="#e74c3c",
    fontsize=10,
    linespacing=1.4,
    arrowprops=dict(arrowstyle="->", color="#e74c3c", lw=1.5),
)

ax2.legend(loc="upper left")

fig.tight_layout()

save_path = save_dir / "08_stacked_and_transport_focus.jpg"
fig.savefig(save_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(
    f"saved: {save_path} | {first_year}-{last_year}, "
    f"transport equipment {pct_growth:+.1f}% ({share_first:.1f}% -> {share_last:.1f}%)"
)
