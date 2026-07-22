import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set font family for Korean text and prevent minus sign clipping
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

# Set the color palette for the background of the plot
region_bg_colors = {
    '수도권': "#D9F8F8", 
    '영남권': "#DCDDF6",
    '충청권': "#E2F4DD", 
    '호남권': '#FFEBEE',    
}

# Load the query result
df = pd.read_csv("NLIC/data/gap_22_23.csv")

# Filter the top 12 cities based on the absolute value of the change to keep the plot clean
df['abs_gap'] = df['물동량_변화량'].abs()

type_mapping = {
    '출발': 'departure',
    '도착': 'arrival'
}
# Separate visualization for '출발' (Departure) and '도착' (Arrival)
for kor_type, eng_type in type_mapping.items():
    type_data = df[df['구분'] == kor_type]
    
    if type_data.empty:
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
    
    plt.axvline(0, color='black', linestyle='--', linewidth=1) # Reference line at 0
    plt.title(f"2022 vs 2023 Cargo Volume Change by Major Cities ({eng_type})", fontsize=15, pad=15)
    plt.xlabel("Change in Cargo Volume (2023 - 2022)", fontsize=11)
    plt.ylabel("City", fontsize=11)
    # plt.grid(axis='x', linestyle='--', alpha=0.5)
    
    save_dir = "NLIC/output" # Change this to the desired directory

    plt.tight_layout()
    save_path = os.path.join(save_dir, f"gap_{eng_type}_22-23.jpg")
    
    # 수정 후 코드
    plt.savefig(save_path, dpi=300, pil_kwargs={'quality': 95})
    plt.close()
