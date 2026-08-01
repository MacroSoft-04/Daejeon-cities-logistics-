import io
import re
from pathlib import Path
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Directory setup
base_dir = Path(".")
save_dir = base_dir / "NLIC" / "output"
save_dir.mkdir(parents=True, exist_ok=True)
data_dir = base_dir / "NLIC" / "data"

# Data loading
data_df = pd.read_csv(data_dir / "cp_yearly_total_amount.csv")
region_df = pd.read_csv(base_dir / "region_mapping.csv")
color_df = pd.read_csv(base_dir / "color_palette.csv")

# Data preprocessing to df_long format
clean_df = data_df.drop(columns=["total_cargo_volume"], errors="ignore")
df_melted = pd.melt(
    clean_df,
    id_vars=["year", "flow_type"],
    var_name="metric_region",
    value_name="value",
)

df_melted[["region", "metric"]] = df_melted["metric_region"].str.rsplit(
    "_", n=1, expand=True
)

df_long = df_melted.pivot(
    index=["year", "flow_type", "region"],
    columns="metric",
    values="value",
).reset_index()
df_long.columns.name = None

# Font and global configurations
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

type_color_map = {"출발": "#17669e", "도착": "#ad5100"}

# Internationalization (I18N) settings
I18N = {
    "ko": {
        "title_main": "수도권 기준 연도·권역별 물동량 비율 변화 (2019-2023)",
        "title_sub": "{type}",
        "type_map": {"출발": "출발", "도착": "도착"},
        "legend_title": "권역",
        "xlabel": "연도",
        "ylabel": "물동량 (백만 톤)",
        "filename": "cp_total_ratio_ko.jpg",
        "year_fmt": lambda yr: f"{yr}년",
        "total_fmt": lambda val: f"총합: {val:.1f}백만",
    },
    "en": {
        "title_main": "Freight Flow Ratio Change by Region for Capital Area (2019-2023)",
        "title_sub": "{type}",
        "type_map": {"출발": "departure", "도착": "arrival"},
        "legend_title": "Region",
        "xlabel": "Year",
        "ylabel": "Freight Flow Amount (Million Tons)",
        "filename": "cp_total_ratio_en.jpg",
        "year_fmt": lambda yr: f"{yr}year",
        "total_fmt": lambda val: f"Total: {val:.1f}M",
    },
}


class ColorMapper:

    def __init__(self, color_df):
        other_row = color_df[color_df["id"].astype(str) == "other"]
        default_other_color = (
            other_row["color_code"].values[0] if not other_row.empty else "#E0E0E0"
        )

        self.color_map = {
            "Others": default_other_color,
            "기타": default_other_color,
        }

        palette_rows = color_df[color_df["id"].astype(str) != "other"]
        self.palette = palette_rows["color_code"].tolist()
        self.color_idx = 0

    def get_color(self, region):
        if region not in self.color_map:
            self.color_map[region] = self.palette[self.color_idx % len(self.palette)]
            self.color_idx += 1
        return self.color_map[region]


color_mapper = ColorMapper(color_df)


def get_region_info(key, lang="en"):
    match = region_df[
        (region_df["key"] == key)
        | (region_df["en_name"] == key)
        | (region_df["kr_name"] == key)
    ]
    if not match.empty:
        row = match.iloc[0]
        return row["en_name"] if lang == "en" else row["kr_name"]
    return key


def prepare_stacked_data(df, f_type, threshold=10.0):
    years = sorted(df["year"].unique())
    processed_list = []

    filtered_df = df[df["flow_type"] == f_type].copy()

    for yr in years:
        yr_df = (
            filtered_df[filtered_df["year"] == yr]
            .sort_values(by="ratio", ascending=True)
            .copy()
        )

        cumsum = yr_df["ratio"].cumsum()
        yr_df["processed_region"] = yr_df["region"]
        yr_df.loc[cumsum <= threshold, "processed_region"] = "Others"

        grouped_df = yr_df.groupby(
            ["year", "flow_type", "processed_region"], as_index=False
        )[["ratio", "vol"]].sum()

        grouped_df.rename(columns={"processed_region": "region"}, inplace=True)
        processed_list.append(grouped_df)

    return pd.concat(processed_list, ignore_index=True)


def generate_multilingual_plots(df_long, data_df, save_dir):
    for lang in ["ko", "en"]:
        cfg = I18N[lang]

        # Create 1x2 subplots (Departure / Arrival)
        fig, axes = plt.subplots(1, 2, figsize=(16, 7.5))
        legend_handles = {}

        for i, gubun in enumerate(["출발", "도착"]):
            ax = axes[i]

            df_stacked = prepare_stacked_data(df_long, f_type=gubun, threshold=10.0)
            years = sorted(df_stacked["year"].unique())

            pivot_ratio = df_stacked.pivot(
                index="year", columns="region", values="ratio"
            ).fillna(0)
            pivot_vol = df_stacked.pivot(
                index="year", columns="region", values="vol"
            ).fillna(0)

            # Position 'Others' at the top of the stack
            categories = [c for c in pivot_ratio.columns if c != "Others"]
            if "Others" in pivot_ratio.columns:
                categories.append("Others")

            x_labels = [cfg["year_fmt"](yr) for yr in years]
            bottoms = np.zeros(len(years))

            # Draw stacked bars by region
            for cat in categories:
                heights = pivot_ratio[cat].values
                vols = pivot_vol[cat].values if cat in pivot_vol else heights

                display_name = get_region_info(cat, lang=lang)
                cat_color = color_mapper.get_color(cat)

                bars = ax.bar(
                    x_labels,
                    vols,
                    bottom=bottoms,
                    width=0.55,
                    color=cat_color,
                    edgecolor="white",
                    linewidth=0.8,
                    label=display_name,
                )

                if display_name not in legend_handles:
                    legend_handles[display_name] = bars[0]

                # Display percentage inside segment (>= 4.0%)
                for idx, (bar, pct) in enumerate(zip(bars, heights)):
                    h = bar.get_height()
                    if h > 0 and pct >= 4.0:
                        y_pos = bottoms[idx] + (h / 2.0)
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            y_pos,
                            f"{pct:.1f}%",
                            ha="center",
                            va="center",
                            fontsize=8.5,
                            fontweight="bold",
                            color="black" if cat == "Others" else "white",
                        )

                bottoms += vols

            # Display total volume text above bars
            max_bar_height = max(bottoms) if len(bottoms) > 0 else 1
            for idx, yr in enumerate(years):
                # data_df에서 flow_type까지 구분해서 가져오는 방식 (필요 시)
                tot_sub = data_df[
                    (data_df["year"] == yr) & (data_df["flow_type"] == gubun)
                ]
                if not tot_sub.empty and "total_cargo_volume" in tot_sub.columns:
                    tot_num = tot_sub["total_cargo_volume"].values[0] / 1_000_000
                else:
                    tot_num = bottoms[idx]

                ax.text(
                    idx,
                    bottoms[idx] + (max_bar_height * 0.03),
                    cfg["total_fmt"](tot_num),
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    color=type_color_map[gubun],
                )

            # Subplot styles
            sub_title = cfg["title_sub"].format(type=cfg["type_map"][gubun])
            ax.set_title(
                sub_title,
                fontsize=15,
                pad=12,
                color=type_color_map[gubun],
                fontweight="bold",
            )
            ax.set_xlabel(cfg["xlabel"], fontsize=11, labelpad=8)
            ax.set_ylabel(cfg["ylabel"], fontsize=11, labelpad=8)
            ax.set_ylim(0, max_bar_height * 1.15)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            ax.set_axisbelow(True)

        # Main title and unified legend
        fig.suptitle(cfg["title_main"], fontsize=17, fontweight="bold", y=0.98)

        fig.legend(
            legend_handles.values(),
            legend_handles.keys(),
            title=cfg["legend_title"],
            loc="center left",
            bbox_to_anchor=(0.91, 0.5),
            fontsize=10,
            title_fontsize=11,
            frameon=True,
        )

        plt.subplots_adjust(left=0.07, right=0.88, wspace=0.22, top=0.88)

        # Save plot
        save_path = save_dir / cfg["filename"]
        plt.savefig(save_path, dpi=300, bbox_inches="tight", pad_inches=0.2)
        plt.close(fig)


# Execution
generate_multilingual_plots(df_long, data_df, save_dir)
