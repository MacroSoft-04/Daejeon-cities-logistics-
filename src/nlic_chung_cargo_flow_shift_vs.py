from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

# 한글 폰트 및 마이너스 기호 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

base_dir = Path(".")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 1. Load Data (UNION ALL 쿼리 결과 CSV)
df_raw = pd.read_csv(data_dir / "nlic_chung_cargo_volume_shift.csv")

# 연도별 변동 데이터 분리 (period_type 기준)
data_map = {
    "21_22": df_raw[df_raw["period_type"] == "2021-2022"].copy(),
    "22_23": df_raw[df_raw["period_type"] == "2022-2023"].copy(),
}

# Subplot 위치 매핑 설정
col_idx_map = {"21_22": 0, "22_23": 1}
row_idx_map = {"출발": 0, "도착": 1}

# 2. Highlight cities setting
highlight_map = {
    "ko": {
        ("21_22", "출발"): ["울산", "수도권", "충남", "충북"],
        ("21_22", "도착"): ["수도권", "충남"],
        ("22_23", "출발"): ["충남", "수도권", "대전"],
        ("22_23", "도착"): ["충남", "수도권"],
    },
    "en": {
        ("21_22", "출발"): ["Ulsan", "Capital Area", "Chungnam", "Chungbuk"],
        ("21_22", "도착"): ["Capital Area"],
        ("22_23", "출발"): ["Chungnam", "Capital Area", "Daejeon"],
        ("22_23", "도착"): ["Chungnam", "Capital Area"],
    },
}

# 3. Multilingual Configuration Dictionary
I18N = {
    "ko": {
        "title_main": "충청도 기준 권역별 화물 물동량 연도별 변동 분석 (2021-2023)",
        "subtitle": "[{year}] 화물 물동량 변동 ({type})",
        "unit_fmt": "{val:+.1f}만",
        "xaxis_fmt": lambda x, pos: f"{int(x/10000)}만" if x != 0 else "0",
        "city_col": "target_city",
        "region_col": "region",
        "type_map": {"출발": "출발", "도착": "도착"},
        "year_map": {"21_22": "2021 vs 2022", "22_23": "2022 vs 2023"},
        "info_box": "* Y: 도시 (권역)  |  단위: 만 톤\n* 수도권: 서울/경기/인천 통합",
        "filename": "11_Chungcheong_cargo_flow_shift_dashboard_2x2_ko.jpg",
    },
    "en": {
        "title_main": "Chungcheong Regional O/D Freight Flow Shift Analysis (2021-2023)",
        "subtitle": "[{year}] Cargo Volume Change ({type})",
        "unit_fmt": "{val:+.1f}k",
        "xaxis_fmt": lambda x, pos: f"{int(x/10000)}k" if x != 0 else "0",
        "city_col": "city_en",
        "region_col": "region_en",
        "type_map": {"출발": "Departure", "도착": "Arrival"},
        "year_map": {"21_22": "2021 vs 2022", "22_23": "2022 vs 2023"},
        "info_box": "* Y: City (Region)  |  Unit: 10k Tons\n* Capital Area: Seoul/Gyeonggi/Incheon",
        "filename": "11_Chungcheong_cargo_flow_shift_dashboard_2x2_en.jpg",
    },
}

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

            plot_data = df[df["direction"] == gubun].copy()
            if plot_data.empty:
                continue

            c_col = cfg["city_col"]
            r_col = cfg["region_col"]

            # Y축 축 라벨 생성 (도시명 + 권역명)
            plot_data["도시_권역"] = plot_data[c_col] + " (" + plot_data[r_col] + ")"

            # gap_vol 기준 내림차순 정렬
            plot_data = plot_data.sort_values(
                by="gap_vol", ascending=False
            ).reset_index(drop=True)

            # 강조 표시 도시 목록
            current_highlights = highlight_map[lang].get((year_key, gubun), [])

            # 바 색상 지정 (강조 도시는 진한 색, 일반 도시는 연한 색)
            # 바 색상 지정 (강조 도시는 진한 색, 일반 도시는 연한 색)
            colors = []
            for idx, row in plot_data.iterrows():
                city_name = str(row[c_col]).strip().lower()
                val = row["gap_vol"]

                # 권역(region)은 제외하고 오직 순수 도시명(city_name)에 대해서만 완전 일치 또는 매칭 검사
                is_highlighted = any(
                    hl.strip().lower() in city_name for hl in current_highlights
                )

                if is_highlighted:
                    colors.append(
                        "#2B5C8F" if val > 0 else "#C44E52"
                    )  # 진한 파랑 / 진한 빨강
                else:
                    colors.append(
                        "#AFC1D4B8" if val > 0 else "#D7B9BA9F"
                    )  # 연한 파랑 / 연한 빨강

            # Barplot 생성
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

            # 축 범위 조절
            x_min, x_max = ax.get_xlim()
            x_range = x_max - x_min
            ax.set_xlim(x_min - x_range * 0.12, x_max + x_range * 0.12)
            ax.xaxis.get_major_formatter().set_scientific(False)

            # 수치 라벨 표시
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

            # 축 및 격자 스타일 설정
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
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(cfg["xaxis_fmt"]))

            # 안내 상자
            ax.text(
                0.02,
                0.88,
                cfg["info_box"],
                transform=ax.transAxes,
                fontsize=9,
                linespacing=1.5,
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

    # 전체 타이틀 설정
    fig.suptitle(cfg["title_main"], fontsize=18, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.95])

    save_path = save_dir / cfg["filename"]
    plt.savefig(save_path, dpi=300, bbox_inches="tight", pil_kwargs={"quality": 95})
    plt.close()
