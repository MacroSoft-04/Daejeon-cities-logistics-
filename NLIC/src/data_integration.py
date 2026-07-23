import pandas as pd
from pathlib import Path

years = ['2019', '2020', '2021', '2022', '2023']
df_list = []

base_dir = Path(".")
raw_data_dir = base_dir / "NLIC" / "rawdata"
data_dir = base_dir / "NLIC" / "data"

#append each year's DataFrame to the list
for year in years:
    filename = Path(raw_data_dir / f"Deajeon_logistics_{year}.csv")
    df = pd.read_csv(filename, index_col='지역')
    df_list.append(df)

# Concatenate all DataFrames in the list along the columns (axis=1)
df_total = pd.concat(df_list, axis=1)

df_total.to_csv(f"{data_dir}/data_logistics_total.csv", encoding='utf-8-sig')