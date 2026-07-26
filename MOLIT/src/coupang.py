from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. Path Settings
base_dir = Path(".")
data_dir = base_dir / "MOLIT" / "data"
save_dir = base_dir / "MOLIT" / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 2. Load Dataset
df_raw = pd.read_csv(data_dir / "coupang.csv")

# 3. set font & color palette
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

COLOR_PALETTE = [
    "#6399D2",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#59A14F",
    "#EDC948",
    "#B07AA1",
    "#FF9DA7",
    "#9C755F",
    "#BAB0AC",
]

# Region name translator for English version
REGION_MAP = {
    "수도권": "Capital Area",
    "기타": "Others",
}

# Multilingual configuration dictionary
I18N = {
    "ko": {
        "title": "권역별 풀필먼트/로지스틱스(FC) 거점 신설 추이 (2019~2025)",
        "xlabel": "연도",
        "ylabel": "신규 거점 등록 건수",
        "legend_title": "권역 구분",
        "total_fmt": "총 {}건",
        "filename": "coupang_region_stacked_ko.jpg",
    },
    "en": {
        "title": "FC Warehouse Registrations by Region (2019-2025)",
        "xlabel": "Year",
        "ylabel": "New Registration Count",
        "legend_title": "Region",
        "total_fmt": "Total: {}",
        "filename": "coupang_region_stacked_en.jpg",
    },
}

# Reshape raw data
df_plot = df_raw.pivot_table(
    index="YEAR", 
    columns="SIDO_GROUP",  # Make sure this matches your CSV column name!
    values="REGISTRATION_COUNT", 
    aggfunc="sum"
).fillna(0)

df_plot = df_plot.apply(pd.to_numeric, errors="coerce").fillna(0)

# Color Mapper (Works with both Korean and English keys)
class ColorMapper:
    def __init__(self, palette):
        self.palette = palette
        self.color_map = {
            "기타": "#E0E0E0", 
            "Others": "#E0E0E0"
        }
        self.color_idx = 0

    def get_color(self, name):
        if name not in self.color_map:
            self.color_map[name] = self.palette[
                self.color_idx % len(self.palette)
            ]
            self.color_idx += 1
        return self.color_map[name]

color_mapper = ColorMapper(COLOR_PALETTE)

# 4. Draw chart (Multilingual Loop)
for lang, cfg in I18N.items():
    # Translate columns for English mode
    if lang == "en":
        df_lang = df_plot.rename(columns=REGION_MAP)
    else:
        df_lang = df_plot.copy()

    # Dynamically push '기타' / 'Others' to the last position (plotted at the TOP)
    other_cols = [c for c in df_lang.columns if c in ["기타", "Others"]]
    main_cols = [c for c in df_lang.columns if c not in ["기타", "Others"]]
    df_lang = df_lang[main_cols + other_cols]

    colors = [color_mapper.get_color(col) for col in df_lang.columns]

    fig, ax = plt.subplots(figsize=(12, 7))
    bottoms = np.zeros(len(df_lang))

    for idx, col in enumerate(df_lang.columns):
        values = df_lang[col].values
        x_labels = [
            f"{yr}yr" if lang == "en" else f"{yr}년" for yr in df_lang.index
        ]

        bars = ax.bar(
            x_labels,
            values,
            bottom=bottoms,
            label=col,
            color=colors[idx],
            width=0.55,
            edgecolor="white",
            linewidth=1,
        )

        # High-contrast text color: White for main bars, Dark for 'Others'
        text_color = "#333333" if col in ["기타", "Others"] else "white"

        # Inner detail labels
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
                    color=text_color,
                )

        bottoms += values

    # Total counts above top bars
    for idx, tot in enumerate(bottoms):
        if tot > 0:
            ax.text(
                idx,
                tot + (max(bottoms) * 0.02),
                cfg["total_fmt"].format(int(tot)),
                ha="center",
                va="bottom",
                fontsize=10.5,
                fontweight="bold",
                color="#222222",
            )

    # Title & Label settings
    ax.set_title(cfg["title"], fontsize=15, pad=20, fontweight="bold")
    ax.set_xlabel(cfg["xlabel"], fontsize=11, labelpad=10)
    ax.set_ylabel(cfg["ylabel"], fontsize=11, labelpad=10)
    ax.set_ylim(0, max(bottoms) * 1.15)

    # Grid & Legend
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    
    # Reverse legend order so top stack matches top legend item
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles[::-1],
        labels[::-1],
        title=cfg["legend_title"],
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        frameon=True,
    )

    # Save chart
    save_path = save_dir / cfg["filename"]
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

print("Charts successfully generated in both KO and EN!")