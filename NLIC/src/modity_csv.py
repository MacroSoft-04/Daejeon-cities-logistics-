import json
import pandas as pd
from pathlib import Path

# Paths setup
base_dir = Path("C:/Users/Minseo/Desktop/folder/DJ_competition")

exist_path = base_dir / "NLIC" / "data" 
add_path = base_dir / "NLIC" / "data" / "skorea_nlic.csv"

target_files = {
    "2021-2022": exist_path / "gap_21_22.csv",
    "2022-2023": exist_path / "gap_22_23.csv",
    "2021": exist_path / "cargo_volume_22.csv",
    "2022": exist_path / "cargo_volume_23.csv",
}

# saving data 
output_dir = base_dir / "NLIC" / "data"

for year, filename in target_files.items():
    if not filename.exists():
            print(f"File not found: {filename}")
            continue
    # Read in data
    exist_data = pd.read_csv(filename, encoding="utf-8-sig")
    add_data = pd.read_csv(add_path, encoding="utf-8-sig")

    # rename column
    add_data = add_data.rename(columns = {'nlic' : '도시명'})

    # merge and sort data
    merged_df = pd.merge(exist_data, add_data, on='도시명', how='left')

    df2 = merged_df.drop('도시명', axis=1)
    df2 = df2.rename(columns = {'skorea' : '도시명'})

    # Get current column names as a list
    cols = list(df2.columns)

    # Move '도시명' to index 2
    cols.remove('도시명')
    cols.insert(2, '도시명')

    # Apply new column order
    df = df2[cols]

    output_file = output_dir / f"{filename.stem}_modified.csv"

    df.to_csv(output_file, index=False, encoding="utf-8-sig")