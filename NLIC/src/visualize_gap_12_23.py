import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# 1. Define directory paths relative to project root
base_dir = Path(".")
json_dir = base_dir / "json"
data_dir = base_dir / "NLIC" / "data"

# Load GeoJSON straight into a GeoDataFrame
korea_map = gpd.read_file(json_dir / "skorea_provinces_geo.json")

# Ensure 'code' in korea_map is treated as string for clean merging
korea_map["code"] = korea_map["code"].astype(str)

# [mapping 2] NLIC name -> korea_map column name (using existing column)
skorea_nlic = pd.read_csv(data_dir / "skorea_nlic.csv")

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

    df["도시명"] = df["name"].map(skorea_nlic)

    # Merge map data with CSV data
    # Use 'name' for standard Korean GeoJSONs (or adjust based on print statement output)
    merged = korea_map.merge(df, on="code", how="left")

    # Plot Choropleth Map
    fig, ax = plt.subplots(figsize=(10, 10))

    merged.plot(
        column="물동량_변화량", 
        ax=ax, 
        legend=True, 
        cmap="OrRd", 
        edgecolor="black",
        missing_kwds={"color": "lightgrey", "label": "No Data"}
        )

    # ax.set_axis_off()  # Removes lat/long axis ticks for cleaner visual
    plt.title(f"South Korea Logistics Gap ({year})", fontsize=15)
    plt.tight_layout()
    plt.show()  
