import pandas as pd
from pathlib import Path
import geopandas as gpd
import json

base_dir = Path("C:/Users/Minseo/Desktop/folder/DJ_competition")
json_dir = base_dir / "json"
data_dir = base_dir / "NLIC" / "data"

korea_map = gpd.read_file(json_dir / "skorea_provinces_geo.json")

# Target files for each year
target_files = {
    "2021-2022": data_dir / "gap_21_22.csv",
    "2022-2023": data_dir / "gap_22_23.csv"
}

# 3. Process and Plot
for year, filename in target_files.items():
    if not filename.exists():
        print(f"File not found: {filename}")
        continue

    df = pd.read_csv(filename)
    
print(korea_map.columns)

# List of actual names in the map data
print("Actual names in map:", korea_map.iloc[:, 0].tolist()) # Usually in the 1st or 2nd column

# List of city names in my CSV after merging/mapping
print("Mapped city names in my CSV:", df["도시명"].unique().tolist())

df["name"] = df["code"].map(korea_map["name"])

print("Actual names in my CSV:", df["name"].unique().tolist())
