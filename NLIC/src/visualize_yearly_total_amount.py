import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'Malgun Gothic'  # Set font to Malgun Gothic for Korean characters
plt.rcParams['axes.unicode_minus'] = False  # Ensure minus sign is displayed correctly

df = pd.read_csv('yearly_total_amount.csv')  # Load the data from a CSV file

df['총 출발량(백만)'] = df['총 출발량'] / 1_000_000  # Convert total departure amount to millions
df['총 도착량(백만)'] = df['총 도착량'] / 1_000_000  # Convert total arrival amount to millions

fig, ax1 = plt.subplots(figsize=(10, 5))  # Create a figure and axis with specified size
ax2 = ax1.twinx()  # Create a secondary y-axis sharing the same x-axis

ax1.set_ylim(0, 12)
ax2.set_ylim(15, 23)

x = np.arange(len(df['연도']))  # Create an array of indices for the x-axis
width = 0.35  # Set the width of the bars

rect1 = ax1.bar(x - width/2, df['총 출발량(백만)'], width, label='총 출발량(백만)', color='skyblue')  # Plot total departure amount
rect2 = ax2.bar(x + width/2, df['총 도착량(백만)'], width, label='총 도착량(백만)', color='salmon')  # Plot total arrival amount

plt.legend(handles=[rect1, rect2], title='구분', bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)  # Set the legend title and location

plt.title('연도별 총 출발량 및 총 도착량 (백만 단위)', fontsize=16, pad=20)  # Set the title of the plot
ax1.set_xlabel('연도', fontsize=12)  # Set the x-axis label
ax1.set_ylabel('총 출발량 (백만 단위)', fontsize=12)  # Set the y-axis label for total departure amount
ax2.set_ylabel('총 도착량 (백만 단위)', fontsize=12)  # Set the y-axis label

ax1.set_xticks(x)  # Set the x-ticks to the indices
ax1.set_xticklabels(df['연도'])  # Set the x

ax1.grid(axis='y', linestyle='--', alpha=0.5)  # Add grid lines to the y-axis

lines1, labels1 = ax1.get_legend_handles_labels()  # Get the legend handles and labels for the first axis
lines2, labels2 = ax2.get_legend_handles_labels()  # Get the legend

for p in ax1.patches: # Add data labels to the bars in the first axis
    height = p.get_height()
    if height > 0:
        ax1.text(p.get_x() + p.get_width()/2., height + 0.2, f'{height:.1f}', ha="center", fontsize=9)

for p in ax2.patches: # Add data labels to the bars in the second axis
    height = p.get_height()
    if height > 0:
        ax2.text(p.get_x() + p.get_width()/2., height + 0.1, f'{height:.1f}', ha="center", fontsize=9)

plt.savefig('yearly_total_amount.png', dpi=300, bbox_inches='tight')  # Save the plot as a PNG file
