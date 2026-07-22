import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path
import matplotlib.colors as mcolors

# Set font family for Korean text and prevent minus sign clipping
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

# 1. Define directory paths relative to project root
base_dir = Path(".")
data_dir = base_dir / "NLIC" / "data"
save_dir = Path("NLIC/output")

# Set the color palette for the background of the plot
region_bg_colors = {
    '수도권': "#D9F8F8", 
    '영남권': "#DCDDF6",
    '충청권': "#E2F4DD", 
    '호남권': '#FFEBEE',    
}

target_files = {
    "2021-2022": data_dir / "gap_21_22_modified.csv",
    "2022-2023": data_dir / "gap_22_23_modified.csv",
}

type_mapping = {
    '출발': 'departure',
    '도착': 'arrival'
}

# 3. Process and Plot
for year, filename in target_files.items():
    if not filename.exists():
        print(f"File not found: {filename}")
        continue

    df = pd.read_csv(filename)

    for kor_type, eng_type in type_mapping.items():
        type_data = df[df['구분'] == kor_type].copy()
        if type_data.empty:
            print(f"No {eng_type} data found")
            continue

        type_data['abs_gap'] = type_data['물동량_변화량'].abs()
        plot_data = type_data.sort_values(by='abs_gap', ascending=False).head(12)
    
        plot_data = plot_data.reset_index(drop=True)
    
        plot_data['도시_권역']=plot_data['도시명']+'('+plot_data['권역']+')'
        
        plot_data=plot_data.sort_values(by='물동량_변화량', ascending=False)
    
        # Create a new figure and axis
        fig, ax = plt.subplots(figsize=(11, 7))
    
        # Set the background color for the plot
        unique_regions = plot_data['권역'].unique()
        current_y_idx = 0
        for region in plot_data['권역']:
            bg_color = region_bg_colors.get(region, '#FFFFFF')
            ax.axhspan(current_y_idx - 0.5, current_y_idx + 0.5, facecolor=bg_color, alpha=0.9, zorder = 0)
            current_y_idx += 1
        
        # Use blue for positive changes and red for negative changes for intuitive visualization
        colors = ['#4C72B0' if x > 0 else '#C44E52' for x in plot_data['물동량_변화량']]
    
        # Create a dictionary to map the city names to colors
        color_dict = dict(zip(plot_data['도시_권역'], colors))

        plt.axvline(0, color='black', linestyle='--', linewidth=1) # Reference line at 0
        plt.title(f"2022 vs 2023 Cargo Volume Change by Major Cities ({eng_type})", fontsize=15, pad=15)
        plt.xlabel("Change in Cargo Volume (2023 - 2022)", fontsize=11)
        plt.ylabel("City", fontsize=11)
        # plt.grid(axis='x', linestyle='--', alpha=0.5)
    sns.barplot(
            data=plot_data, 
            x='물동량_변화량', 
            y='도시_권역', 
            hue='도시_권역',       # Added to follow the latest Seaborn formatting guidelines
            palette=colors,
            legend=False,       # Hides the redundant legend
            ax=ax,
            zorder = 1
        )    
    
    fig.suptitle("권역별 물동량 비율 변화", fontsize=20, y=1.05)
    fig.subplots_adjust(left=0.08, right=0.86, wspace=0.35)
    save_path = save_dir / f"gap_merged.jpg"
    plt.savefig(save_path, dpi = 300, bbox_inches="tight", pad_inches=0.4)
    plt.close()
    plt.savefig(save_path, dpi=300, pil_kwargs={'quality': 95})
    plt.close()