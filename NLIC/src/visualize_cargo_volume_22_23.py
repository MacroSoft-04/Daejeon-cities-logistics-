import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
import seaborn as sns

plt.rcParams['font.family'] = 'Malgun Gothic'  # Set font to Malgun Gothic for Korean characters
plt.rcParams['axes.unicode_minus'] = False  # Ensure minus sign is displayed correctly

# set background colors by region
region_colors = {
    '수도권': "#6DD8D8", 
    '영남권': "#6569E0",
    '충청권': "#97D485", 
    '호남권': "#F1C497",    
    '기타': "#858181"
}

# English mapping for type
type_mapping = {
    '출발': 'departure',
    '도착': 'arrival'
}

# find the target files
data_dir = Path("NLIC/data")

# target files for each year
target_files = {
    2022: data_dir/"cargo_volume_22.csv",
    2023: data_dir/"cargo_volume_23.csv"
}

# save directory
save_dir = Path("NLIC/output")

for year, filename in target_files.items():
    if not os.path.exists(filename):
        print(f"there is no {filename} file")
        continue
    df = pd.read_csv(filename)

    # visualize departure and arrival
    for kor_type, eng_type in type_mapping.items():
        type_data = df[df['구분'] == kor_type].copy()

        if type_data.empty:
            continue
        # extract top 12 cities by cargo volume
        type_data['abs_volume'] = type_data['물동량'].abs()
        plot_data = type_data.sort_values(by='abs_volume', ascending=False).head(12)
        plot_data = plot_data.reset_index(drop=True) 

        # create a label for each city
        # city name (region)
        plot_data['도시_권역'] = plot_data['도시명'] + '(' + plot_data['권역'] + ')'

        # sort by volume
        plot_data = plot_data.sort_values(by='물동량', ascending=False)

        # Set up the figure size
        fig, ax = plt.subplots(figsize=(11, 7))

        # Set the bar colors
        colors = [region_colors.get(reg, '#CCCCCC') for reg in plot_data['권역']]
        # Draw the barplot
        sns.barplot(
            data=plot_data, 
            x='물동량', 
            y='도시_권역', 
            hue='도시_권역', 
            palette=colors,
            ax=ax
        )

        
        active_regions = plot_data['권역'].unique()
        legend_handles = []
        for region in active_regions:
            if region in region_colors:
                patch = mpatches.Patch(color=region_colors[region], label=region)
                legend_handles.append(patch)
        ax.legend(
            handles=legend_handles, 
            title='권역', 
            bbox_to_anchor=(1.05, 1), 
            loc='upper left', 
            borderaxespad=0.,
            frameon=True,
            facecolor = 'white',
            edgecolor = 'gray')  # Set the legend title and location
        

        plt.axvline(0, color='black', linestyle='--', linewidth=1) 
        plt.title(f"{year} Cargo Volume by Major Cities ({eng_type})", fontsize=15, pad=15)
        plt.xlabel("Cargo Volume", fontsize=11)
        plt.ylabel("City", fontsize=11)

        def millions_formatter(x, pos):
            return f'{x*1e-6:.1f}M' if x != 0 else '0'
            
        ax.xaxis.set_major_formatter(FuncFormatter(millions_formatter))
        plt.xlabel("물동량 (단위: 백만)", fontsize=11)

        ax.grid(axis='x', linestyle='--', alpha=0.5, zorder=0)

        for p in ax.patches: # Add data labels to the bars in the axis
            width = p.get_width()
            if abs(width) > 0:
                x_pos = width + (max(plot_data['물동량']) * 0.01)
                y_pos = p.get_y() + p.get_height()/2.
                label_text = f'{width/1000000:.1f}만'
                ax.text(x_pos, y_pos, label_text,va = "center", ha="left", fontsize=9, color = "black")

        
        plt.tight_layout()

        save_path = save_dir / f"volume_{eng_type}_{str(year)[2:]}.jpg"
        
        plt.savefig(save_path, dpi=300, pil_kwargs={'quality': 95})
        plt.close()