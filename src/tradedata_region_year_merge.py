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
import numpy as np
import pandas as pd
import random

base_dir = Path(".")
origin_dir = base_dir / "data/raw/trade_data"
data_dir = base_dir / "data/processed"
origin_dir.mkdir(parents=True, exist_ok=True)
hs_cat = pd.read_csv(data_dir / "codebook_hs_categories.csv", dtype={"HS코드": str})
save_path = data_dir / "tradedata_2000_2025_merged.csv"

dfs = []

files = sorted(origin_dir.glob("*.csv"))
random.seed(42)
preview = set(random.sample(files, min(1, len(files))))

for file_path in files:
    # append the filename, remove '총계'
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

    if file_path in preview:
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
    # convert data types
    if "HS코드" in final_df.columns:
        hs_col = final_df["HS코드"].astype(str).str.strip()
        hs_col = hs_col.str.replace(r"\*\)", "", regex=True).str.strip()
        hs_col = hs_col.str.replace(r"\.0$", "", regex=True)
        final_df["HS코드"] = hs_col.str.zfill(2)
    if "기간" in final_df.columns:
        years = pd.to_numeric(final_df["기간"], errors="coerce")
        unparseable = final_df.loc[years.isna(), "기간"]
        if not unparseable.empty:
            print(f"\n{len(unparseable)} rows with an unparseable 기간:")
            print(unparseable.value_counts())
        final_df = final_df.loc[years.notna()].copy()
        final_df["기간"] = years.dropna().astype(int)

    # verify that the data is clean
    duplicated = final_df.duplicated(["지역", "기간", "HS코드"], keep=False)
    if duplicated.any():
        print(f"⚠️ {duplicated.sum()} rows share a duplicated key:")
        print(final_df.loc[duplicated, ["지역", "기간", "HS코드"]].head(10).to_string())

    null_counts = final_df.isna().sum()
    assert (
        not null_counts.any()
    ), f"Source data should have no nulls:\n{null_counts[null_counts > 0]}"

    df_merged = final_df.merge(hs_cat, on="HS코드", how="left", validate="many_to_one")

    def report_missing_labels(df, label_cols, code_col="HS코드"):
        """Report which chapters lack each label, not just how many rows are null."""
        for col in label_cols:
            if col not in df.columns:
                print(f"{col}: column not present")
                continue

            missing = df.loc[df[col].isna(), code_col]
            if missing.empty:
                print(f"{col}: complete")
            else:
                chapters = sorted(missing.unique())
                print(f"{col}: {len(missing)} rows across chapters {chapters}")

    report_missing_labels(df_merged, ["품목명", "품목약칭_TRASS"])

    df_merged = df_merged.sort_values(["지역", "기간", "HS코드"], ignore_index=True)
    df_merged.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(
        f"Merged {len(dfs)} files into {len(df_merged):,} rows. Saved to: {save_path.resolve()}"
    )
