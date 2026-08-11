"""
====================================================================
* Author: Minseo Kim
* Data Sources:
    - NLIC (National Land Investment Corporation)
* visualizaiton:
    - Line Chart
    - Import & Export Volumes of Regional Raw Materials by Category
    - Capital Area (Seoul, Incheon, Gyeonggi), Daejeon, Chungchung(excl. DJ)
* Output: 07_raw_materials_detail.jpg
====================================================================
"""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from adjustText import adjust_text

# 한글 폰트 및 마이너스 깨짐 설정
plt.rc("font", family="Malgun Gothic")  # Windows: Malgun Gothic / Mac: AppleGothic
plt.rc("axes", unicode_minus=False)

base_dir = Path(".")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 1. 데이터 불러오기 (행 구조로 변경된 데이터)
df = pd.read_csv(data_dir / "nlictr_raw_meterial_detail_vs07.csv")
color_df = pd.read_csv("color_palette.csv")

# 물동량 단위 조정 (천 톤)
df["cargo_vol_k"] = df["cargo_vol"] / 1000

# 2. 권역 목록
regions = df["region_kr"].unique()

unique_commodities = df["commodity"].unique()
palette = sns.color_palette("tab10", len(unique_commodities))
commodity_color_map = {
    commodity: color for commodity, color in zip(unique_commodities, palette)
}

# 서브플롯 생성 (권역별로 1개씩)
fig, axes = plt.subplots(len(regions), 1, figsize=(11, 4 * len(regions)), sharex=False)
if len(regions) == 1:
    axes = [axes]

# 💡 X축 좌표 대칭 설정
# 왼쪽(반출): -3(23년) <- -2(22년) <- -1(21년) <- 0(20년 기준)
# 오른쪽(반입): 0(20년 기준) -> 1(21년) -> 2(22년) -> 3(23년)
x_map_in = {2020: 0, 2021: 1, 2022: 2, 2023: 3}
x_map_out = {2020: 0, 2021: -1, 2022: -2, 2023: -3}


for ax, region in zip(axes, regions):

    region_df = df[df["region_kr"] == region]

    # 중앙 기준선 (2020년)
    ax.axvline(0, color="black", linestyle="-", linewidth=2, alpha=0.7)

    # 품목(rank_num & commodity)별로 선 그리기
    items = region_df[["rank_num", "commodity"]].drop_duplicates().values

    # 💡 좌/우 범례에 넣을 선(Line) 객체 핸들을 담아둘 리스트
    in_handles, in_labels = [], []
    out_handles, out_labels = [], []
    texts = []
    extra_artists = []  # list for put legend outside of the plot

    for rank, commodity in items:
        item_df = region_df[
            (region_df["rank_num"] == rank) & (region_df["commodity"] == commodity)
        ]
        line_color = commodity_color_map[commodity]

        # ------------------- 1) 반입 (오른쪽 +X 영역) -------------------
        in_df = item_df[item_df["flow_type"] == "반입"].sort_values("year")
        if not in_df.empty:
            x_vals = [x_map_in[y] for y in in_df["year"]]
            y_vals = in_df["cargo_vol_k"].values

            # 꺾은선 그리기
            (line_in,) = ax.plot(
                x_vals,
                y_vals,
                marker="o",
                linewidth=2,
                markersize=6,
                label=f"{commodity}",
                color=line_color,
            )
            # 핸들 저장
            in_handles.append(line_in)
            in_labels.append(f"{commodity}")

            # 데이터 값 텍스트 표기
            for x, y, year in zip(x_vals, y_vals, in_df["year"]):
                if y > 300:
                    t = ax.text(
                        x,
                        y,
                        f"{y:,.0f}",
                        ha="center",
                        va="center",
                        fontsize=8,
                    )
                    texts.append(t)
        # ------------------- 2) 반출 (왼쪽 -X 영역) -------------------
        out_df = item_df[item_df["flow_type"] == "반출"].sort_values("year")
        if not out_df.empty:
            x_vals = [x_map_out[y] for y in out_df["year"]]
            y_vals = out_df["cargo_vol_k"].values

            # 반출은 똑같은 색상에 점선(--)으로 구분감을 줌
            (line_out,) = ax.plot(
                x_vals,
                y_vals,
                marker="s",
                linestyle="--",
                linewidth=2.5,
                markersize=6,
                label=f"{commodity}",
                color=line_color,
            )

            # 핸들 저장
            out_handles.append(line_out)
            out_labels.append(f"{commodity}")

            # 데이터 값 텍스트 표기
            for x, y, year in zip(x_vals, y_vals, out_df["year"]):
                if year != 2020 and y > 300:
                    t = ax.text(
                        x,
                        y,
                        f"{y:,.0f}",
                        ha="center",
                        va="center",
                        fontsize=8,
                    )
                    texts.append(t)

    if texts:
        adjust_text(
            texts,
            ax=ax,
            arrowprops=dict(arrowstyle="-", color="gray", lw=0.5, alpha=0.7),
            only_move={"text": "y"},  # 좌우 X축 좌표는 유지하고 Y축 수직으로만 밀어내기
        )

    # 1. 오른쪽 외부 (반입 범례)
    if in_handles:
        leg_in = ax.legend(
            in_handles,
            in_labels,
            title="[반입 품목]",
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            fontsize=8,
            title_fontsize=9,
            frameon=True,
        )
        # 💡 [핵심 해결 2] 첫 번째 범례를 레이어에 고정해 두 번째 범례에 덮어씌워지지 않게 방지!
        ax.add_artist(leg_in)
        extra_artists.append(leg_in)

    # 2. 왼쪽 외부 (반출 범례)
    if out_handles:
        leg_out = ax.legend(
            out_handles,
            out_labels,
            title="[반출 품목]",
            loc="upper right",
            bbox_to_anchor=(-0.12, 1),
            fontsize=8,
            title_fontsize=9,
            frameon=True,
        )
        extra_artists.append(leg_out)

    # X축 눈금 및 라벨 다듬기 (좌/우 연도 대칭 표기)
    ax.set_xticks([-3, -2, -1, 0, 1, 2, 3])
    ax.set_xticklabels(
        [
            "'23년",
            "'22년",
            "'21년",
            "2020년\n(기준)",
            "'21년",
            "'22년",
            "'23년",
        ],
        fontsize=9,
        fontweight="bold",
    )

    # 좌/우 구획 배경색 약간 넣어서 유출/유입 구분 강조
    xlim = ax.get_xlim()
    ax.axvspan(-3.5, 0, color="red", alpha=0.03)  # 반출 영역 (연한 빨강)
    ax.axvspan(0, 3.5, color="blue", alpha=0.03)  # 반입 영역 (연한 파랑)

    # 상단 텍스트 라벨 (반출 / 반입 방향)
    ax.text(
        -1.5,
        ax.get_ylim()[1] * 0.9,
        "← 반출 (OUT)",
        ha="center",
        fontsize=11,
        fontweight="bold",
        color="darkred",
    )
    ax.text(
        1.5,
        ax.get_ylim()[1] * 0.9,
        "반입 (IN) →",
        ha="center",
        fontsize=11,
        fontweight="bold",
        color="darkblue",
    )

    # 서브플롯 타이틀 및 범례
    ax.set_title(
        f"■ {region} 주요 품목 물동량 추이",
        fontsize=12,
        fontweight="bold",
        loc="left",
    )
    ax.set_ylabel("물동량 (천 톤)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4)

# 전체 타이틀
fig.suptitle(
    "2020~2023년 권역별 반입(오른쪽) / 반출(왼쪽) 물동량 양방향 추이",
    fontsize=14,
    fontweight="bold",
    y=1,
)

plt.tight_layout()

renderer = fig.canvas.get_renderer()
bbox = fig.get_window_extent(renderer=renderer).transformed(
    fig.dpi_scale_trans.inverted()
)

# 3. 💡 [핵심] 차트는 가만히 두고, 도화지 포커스 상자만 오른쪽으로 밀기!
# (x0, y0, x1, y1) -> x1(오른쪽 끝)을 +0.8인치만큼 오른쪽으로 확 넓혀줍니다.
from matplotlib.transforms import Bbox

shift_right = 0.6  # 👈 오른쪽 잘리는 정도에 따라 0.5 ~ 1.2 정도로 조절해보세요!
shift_bottom = 0.7  # 👈 아래 잘리는 정도에 따라 0.1 ~ 0.4 정도로 조절해보세요!
shift_top = 0.4
custom_bbox = Bbox.from_extents(
    bbox.x0, bbox.y0, bbox.x1 + shift_right, bbox.y1 + shift_top
)

# 6. 저장
save_path = save_dir / "07_raw_materials_detail.jpg"
plt.savefig(
    save_path,
    dpi=300,
    bbox_extra_artists=extra_artists,
    bbox_inches=custom_bbox,
    pad_inches=0.3,
)
