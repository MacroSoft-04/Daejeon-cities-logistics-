from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns

# Korean font setup & minus sign display
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

base_dir = Path("./NLIC")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 1. Load Data
data_map = {
    "21_22": pd.read_csv(data_dir / "gap_21_22.csv"),
    "22_23": pd.read_csv(data_dir / "gap_22_23.csv"),
}

# 2. Highlight cities setting for each language, year, and type
highlight_map = {
    "ko": {
        ("21_22", "출발"): ["대전"],
        ("21_22", "도착"): ["서울", "경기", "대전"],
        ("22_23", "출발"): ["대전"],
        ("22_23", "도착"): ["충남"],
    },
    "en": {
        ("21_22", "출발"): ["Daejeon"],
        ("21_22", "도착"): ["Seoul", "Gyeonggi", "Daejeon"],
        ("22_23", "출발"): ["Daejeon"],
        ("22_23", "도착"): ["Chungnam"],
    },
}

# 3. Multilingual Configuration Dictionary
I18N = {
    "ko": {
        "title_main": "권역별 화물 물동량 연도별 변동 분석 (2021-2023)",
        "subtitle": "[{year}] 화물 물동량 변동 ({type})",
        "info_box": "Y: 도시 (권역)  |  단위: 만 톤",
        "unit_fmt": "{val:+.1f}만",
        "xaxis_fmt": lambda x, pos: f"{int(x/10000)}만" if x != 0 else "0",
        "city_col": "city",
        "region_col": "region",
        "etc_replace": (r"기타 \(13개 지자체\)\(기타\)", "기타 (13개 지자체)"),
        "type_map": {"출발": "출발", "도착": "도착"},
        "year_map": {"21_22": "2021 vs 2022", "22_23": "2022 vs 2023"},
        "filename": "cargo_flow_shift_dashboard_2x2_ko.jpg",
    },
    "en": {
        "title_main": "Regional O/D Freight Flow Shift Analysis (2021-2023)",
        "subtitle": "[{year}] Cargo Volume Change ({type})",
        "info_box": "Y: City (Region)  |  Unit: 10k Tons",
        "unit_fmt": "{val:+.1f}k",
        "xaxis_fmt": lambda x, pos: f"{int(x/10000)}k" if x != 0 else "0",
        "city_col": "city_en",
        "region_col": "region_en",
        "etc_replace": (r"Others \(13 Local Govs\)\(Others\)", "Others (13 Local Govs)"),
        "type_map": {"출발": "Departure", "도착": "Arrival"},
        "year_map": {"21_22": "2021 vs 2022", "22_23": "2022 vs 2023"},
        "filename": "cargo_flow_shift_dashboard_2x2_en.jpg",
    },
}

col_idx_map = {"21_22": 0, "22_23": 1}
row_idx_map = {"출발": 0, "도착": 1}

# 4. Generate Korean and English Dashboard Consecutively
for lang in ["ko", "en"]:
    cfg = I18N[lang]
    fig, axes = plt.subplots(2, 2, figsize=(20, 11))

    for year_key, df in data_map.items():
        if df.empty:
            continue

        col_i = col_idx_map[year_key]
        year_label = cfg["year_map"][year_key]

        for gubun, row_i in row_idx_map.items():
            ax = axes[row_i][col_i]
            type_label = cfg["type_map"][gubun]

            plot_data = df[df["구분"] == gubun].copy()
            if plot_data.empty:
                continue

            # Dynamically select localized columns based on current language setting
            c_col = cfg["city_col"]
            r_col = cfg["region_col"]

            plot_data["도시_권역"] = (
                plot_data[c_col] + "(" + plot_data[r_col] + ")"
            )
            plot_data["도시_권역"] = plot_data["도시_권역"].str.replace(
                cfg["etc_replace"][0], cfg["etc_replace"][1], regex=True
            )
            plot_data = plot_data.sort_values(
                by="gap_vol", ascending=False
            ).reset_index(drop=True)

            # Get highlight cities for current language and cell
            current_highlights = highlight_map[lang].get((year_key, gubun), [])

            # Set bar colors
            colors = []
            for idx, row in plot_data.iterrows():
                city_name = row[c_col]  # Match city columns based on target language
                val = row["gap_vol"]

                if city_name in current_highlights:
                    colors.append("#2B5C8F" if val > 0 else "#C44E52")
                else:
                    colors.append("#D7B9BA9F")

            # Render Barplot
            sns.barplot(
                data=plot_data,
                x="gap_vol",
                y="도시_권역",
                hue="도시_권역",
                palette=colors,
                legend=False,
                ax=ax,
                zorder=1,
            )

            # Adjust margins & disable scientific notation
            x_min, x_max = ax.get_xlim()
            x_range = x_max - x_min
            ax.set_xlim(x_min - x_range * 0.12, x_max + x_range * 0.12)
            ax.xaxis.get_major_formatter().set_scientific(False)

            # Add value labels
            for idx, row in plot_data.iterrows():
                val = row["gap_vol"]
                val_in_10k = val / 10000.0
                val_text = cfg["unit_fmt"].format(val=val_in_10k)

                offset = x_range * 0.02
                x_pos = val + offset if val >= 0 else val - offset
                align = "left" if val >= 0 else "right"

                ax.text(
                    x_pos,
                    idx,
                    val_text,
                    va="center",
                    ha=align,
                    fontsize=10,
                    fontweight="bold",
                    zorder=3,
                )

            # Axis & grid styling
            ax.axvline(0, color="black", linestyle="--", linewidth=1, zorder=2)
            ax.set_title(
                cfg["subtitle"].format(year=year_label, type=type_label),
                fontsize=14,
                fontweight="bold",
                pad=12,
            )

            ax.set_xlabel("", fontsize=0)
            ax.set_ylabel("", fontsize=0)
            ax.grid(axis="x", linestyle=":", alpha=0.6, zorder=0)
            ax.xaxis.set_major_formatter(
                ticker.FuncFormatter(cfg["xaxis_fmt"])
            )

            # Top-left info box
            ax.text(
                0.02,
                0.92,
                cfg["info_box"],
                transform=ax.transAxes,
                fontsize=9,
                color="#444444",
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="white",
                    edgecolor="#CCCCCC",
                    alpha=0.8,
                ),
                zorder=4,
            )

    # Super Title
    fig.suptitle(
        cfg["title_main"], fontsize=18, fontweight="bold", y=0.98
    )

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])

    save_path = save_dir / cfg["filename"]
    plt.savefig(
        save_path, dpi=300, bbox_inches="tight", pil_kwargs={"quality": 95}
    )
    plt.close()  # Memory release
