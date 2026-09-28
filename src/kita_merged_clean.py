"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Turn the parsed KITA panel into monthly and yearly regional datasets:
      fold 충남+세종, convert units, derive balance and unit-value metrics.
* Input:
    - data/interim/kita_panel.csv
* Output:
    - data/processed/kita_regional_monthly.csv
    - data/processed/kita_regional_yearly.csv
* Notes:
    - Monetary values go from thousand USD to million USD; weights from kg
      to thousand tons.
    - 수지_금액 is KITA's published figure; 수지_중량 and 중량비 are derived.
    - 충남+세종 is appended before any derivation so its 단가 and 수지 come from
      the same code as every other region. KITA books 세종 inside 충남 until
      July 2012, so only the folded series keeps one boundary across the split.
    - Monthly rows are checked against the published yearly rows before writing.
====================================================================
"""

import re
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MONTHLY_SAMPLE = PROCESSED_DIR / "kita_regional_monthly.csv"
YEARLY_SAMPLE = PROCESSED_DIR / "kita_regional_yearly.csv"

MONTHLY_PATH = PROCESSED_DIR / "kita_regional_monthly_cleaned.csv"
YEARLY_PATH = PROCESSED_DIR / "kita_regional_yearly_cleaned.csv"

FOLDED_REGIONS = ["충남", "세종"]
FOLDED_LABEL = "충남+세종"
FOLD_KEYS = ["집계단위", "연도", "월", "년월"]
# 증감률 is left out on purpose: a rate can't be summed, so folded rows get NaN.
SUMMABLE = ["수출_금액", "수입_금액", "수출_중량", "수입_중량", "수지"]
SOURCE_LEVELS = ["수출_금액", "수입_금액", "수출_중량", "수입_중량"]
ID_COLUMNS = ["지역명", "연도", "월", "연월"]


def add_balance_columns(panel):
    """Weight balance isn't published, but it's what tells you which direction
    the cargo actually runs heavier."""
    panel = panel.rename(columns={"수지": "수지_금액"})
    panel["수지_중량"] = panel["수출_중량"] - panel["수입_중량"]
    panel["중량비_수입대수출"] = panel["수입_중량"] / panel["수출_중량"]
    return panel


def add_folded_region(panel):
    folded = (
        panel[panel["지역명"].isin(FOLDED_REGIONS)]
        # 연간 rows have no 월, and dropna=False keeps those groups.
        .groupby(FOLD_KEYS, as_index=False, dropna=False)[SUMMABLE]
        .sum(min_count=1)
        .assign(지역명=FOLDED_LABEL)
    )
    return pd.concat([panel, folded], ignore_index=True)


def check_monthly_against_yearly(panel):
    for col in SOURCE_LEVELS:
        summed = (
            panel[panel["집계단위"] == "월간"].groupby(["지역명", "연도"])[col].sum()
        )
        published = panel[panel["집계단위"] == "연간"].set_index(["지역명", "연도"])[
            col
        ]
        diff = (summed - published).abs()
        print(
            f"{col}: max abs {diff.max():,.1f}, max rel {(diff / published.abs()).max():.2%}"
        )
