from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Korean font setup
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

save_dir = Path("./KTDB/output")
save_dir.mkdir(parents=True, exist_ok=True)

# Multilingual text dictionary
I18N = {
    "ko": {
        "regions": ["서울", "대전", "경기", "충남"],
        "title": "[KOTI] 주요 권역별 화물자동차 OD 통행 비율 (%)",
        "xlabel": "도착지 (Destination)",
        "ylabel": "출발지 (Origin)",
        "caption": "* 출처: 한국교통연구원(KOTI) 『제5권 전국 화물 OD 본조사』(2022)",
        "filename": "koti_od_heatmap_ko.jpg",
    },
    "en": {
        "regions": ["Seoul", "Daejeon", "Gyeonggi", "Chungnam"],
        "title": "[KOTI] Freight Truck OD Traffic Ratio by Major Region (%)",
        "xlabel": "Destination",
        "ylabel": "Origin",
        "caption": "* Source: KOTI 『The 5th National Freight OD Survey』(2022)",
        "filename": "koti_od_heatmap_en.jpg",
    },
}

# 1. OD Data
od_data = [
    [6.2, 0.0, 2.3, 0.1],
    [0.0, 1.8, 0.1, 0.3],
    [2.3, 0.2, 14.3, 0.6],
    [0.1, 0.3, 0.6, 4.9],
]

# 2. Automated loop to generate Korean and English versions consecutively
for lang in ["ko", "en"]:
    cfg = I18N[lang]
    df_od = pd.DataFrame(od_data, index=cfg["regions"], columns=cfg["regions"])

    fig, ax = plt.subplots(figsize=(8, 7.5))

    sns.heatmap(
        df_od,
        annot=True,
        fmt=".1f",
        cmap="Blues",
        cbar=True,
        linewidths=1,
        linecolor="white",
        annot_kws={"size": 11, "weight": "bold"},
        ax=ax,
    )

    ax.set_title(cfg["title"], fontsize=13, fontweight="bold", pad=20)
    ax.set_xlabel(cfg["xlabel"], fontsize=11, fontweight="bold", labelpad=12)
    ax.set_ylabel(cfg["ylabel"], fontsize=11, fontweight="bold", labelpad=12)

    ax.text(
        0.0,
        -0.1,
        cfg["caption"],
        transform=ax.transAxes,
        fontsize=9,
        color="#555555",
        style="italic",
        verticalalignment="top",
        linespacing=1.4,
    )

    plt.tight_layout()
    save_path = save_dir / f"2022_{cfg['filename']}"
    plt.savefig(
        save_path, dpi=300, bbox_inches="tight", pil_kwargs={"quality": 95}
    )
    plt.close()  # Release memory