"""
====================================================================
* Author: Minseo Kim
* Purpose:
    - Aggregate regional trade data CSV files into a unified dataset
    - Maintain strict 2-digit zero-padded string formatting for HS codes
    - Complete the Cartesian grid (시도명 x 기간 x HS코드) and fill
      missing values with zeroes

* Input:
    - data/raw/trade_data/*.csv

* Output:
    - data/processed/tradedata_2000_2025_raw.csv

* Notes:
    - Preserves HS codes as strings to prevent loss of leading zeros
    - Uses MultiIndex reindexing to ensure a completely balanced grid
====================================================================
"""

from pathlib import Path
import numpy as np  # 안 써도 상관없지만 유지
import pandas as pd

base_dir = Path(".")
origin_dir = base_dir / "data/raw/trade_data"
data_dir = base_dir / "data/processed"
origin_dir.mkdir(parents=True, exist_ok=True)


DEBUG = False

dfs = []

for file_path in origin_dir.glob("*.csv"):
    filename = file_path.stem
    parts = file_path.name.split("_")

    if len(parts) >= 3:
        region_name = "_".join(parts[1:-1])
    else:
        region_name = parts[1] if len(parts) > 1 else "unknown"

    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="cp949")

    if DEBUG:
        print(f"File: {file_path.name} | Columns: {df.columns.tolist()}")

    df["지역"] = region_name
    if "기간" in df.columns:
        clean_df = df[df["기간"] != "총계"].copy()
    else:
        clean_df = df.copy()

    dfs.append(clean_df)

if dfs:
    concat_df = pd.concat(dfs, ignore_index=True)
    final_df = concat_df.rename(columns=lambda x: x.replace(" ", ""))

    if "HS코드" in final_df.columns and not DEBUG:
        hs_col = final_df["HS코드"].astype(str).str.strip()
        hs_col = hs_col.str.replace(r"\*\)", "", regex=True).str.strip()
        hs_col = hs_col.str.replace(r"\.0$", "", regex=True)
        final_df["HS코드"] = hs_col.str.zfill(2)
    if "기간" in final_df.columns:
        final_df["기간"] = pd.to_numeric(final_df["기간"], errors="coerce")
    grid_keys = ["지역", "기간", "HS코드"]

    if all(col in final_df.columns for col in grid_keys):
        all_regions = final_df["지역"].unique()
        all_years = final_df["기간"].dropna().astype(int).unique()
        all_codes = final_df["HS코드"].unique()

        full_index = pd.MultiIndex.from_product(
            [all_regions, all_years, all_codes], names=grid_keys
        )

        final_df = final_df.set_index(grid_keys).reindex(full_index).reset_index()

        trade_metrics = [
            col
            for col in [
                "수출건수(건)",
                "수출금액(천달러)",
                "수입건수(건)",
                "수입금액(천달러)",
                "무역수지",
            ]
            if col in final_df.columns
        ]
        final_df[trade_metrics] = final_df[trade_metrics].fillna(0)

        if "품목명" in final_df.columns:
            hs_to_name = (
                final_df[["HS코드", "품목명"]]
                .dropna()
                .drop_duplicates(subset=["HS코드"])
                .set_index("HS코드")["품목명"]
            )
            final_df["품목명"] = final_df["품목명"].fillna(
                final_df["HS코드"].map(hs_to_name)
            )

    save_path = data_dir / "tradedata_2000_2025_raw.csv"
    final_df = final_df.sort_values(by=["지역", "기간"], ignore_index=True)
    final_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"Successfully processed {len(dfs)} files. Saved to: {save_path.resolve()}")
else:
    print("No CSV files found in the origin directory. Check your path.")
