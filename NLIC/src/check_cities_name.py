import json
import pandas as pd
from pathlib import Path

# Paths setup
base_dir = Path("C:/Users/Minseo/Desktop/folder/DJ_competition")
json_path = base_dir / "json" / "skorea_provinces_geo_simple.json"
csv_path = base_dir / "NLIC" / "data" / "data_logistics_cleaned.csv"
output_dir = base_dir / "NLIC" / "data"

# 1. Read GeoJSON properties into DataFrame
with open(json_path, "r", encoding="utf-8") as f:
    json_data_dict = json.load(f)

features = json_data_dict["features"]
json_df = pd.DataFrame([item["properties"] for item in features])

# Sort json_df cleanly by province name
json_df = json_df.sort_values("name").reset_index(drop=True)

names = json_df["name"].tolist()
codes = json_df["code"].tolist()
print("GeoJSON Names:", names)
print("GeoJSON Codes:", codes)

# 2. Read CSV file and extract unique target regions
csv_df = pd.read_csv(csv_path, encoding="utf-8-sig") 
target = sorted(csv_df["대상지역"].dropna().unique().tolist())
print("Target Regions:", target)

# 3. Compare sets
skorea_set = sorted(set(names))
nlic_set = sorted(set(target))

print(f"GeoJSON count: {len(skorea_set)} | NLIC count: {len(nlic_set)}")

# Note: If skorea_set and nlic_set have different lengths, 
# pd.DataFrame() will throw a ValueError unless wrapped or padded.
# Using pd.concat or zip handles uneven lengths safely:
df_total = pd.DataFrame({
    "skorea": pd.Series(skorea_set),
    "nlic": pd.Series(nlic_set),
    "code": pd.Series(codes)
})

save_path = output_dir / "skorea_nlic.csv"
df_total.to_csv(save_path, index=False, encoding="utf-8-sig")
print(f"Successfully saved to: {save_path}")