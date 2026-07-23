import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.ticker as ticker

# 한글 폰트 설정 및 마이너스 기호 깨짐 방지
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False 

base_dir = Path("./NLIC")
data_dir = base_dir / "data"
save_dir = base_dir / "output"
save_dir.mkdir(parents=True, exist_ok=True)

# 데이터 로드
data_map = {
    '21_22': pd.read_csv(data_dir / "gap_organization_21_22.csv"),
    '22_23': pd.read_csv(data_dir / "gap_organization_22_23.csv")
}

fig, axes = plt.subplots(2, 2, figsize=(20, 11))

# 각 차트 위치(연도, 구분)별로 강조할 핵심 도시 지정
highlight_map = {
    ('21_22', '출발'): ['대전'],   # 예: 특정 주요 변동 도시만
    ('21_22', '도착'): ['서울', '경기', '대전'],
    ('22_23', '출발'): ['대전'],                        # 22-23은 변화가 극심한 대전만 강조
    ('22_23', '도착'): ['충남']                         # 22-23 도착은 유일 반등한 충남만 강조
}

col_idx_map = {'21_22': 0, '22_23': 1}
row_idx_map = {'출발': 0, '도착': 1}
type_eng_map = {'출발': 'departure', '도착': 'arrival'}

for year_key, df in data_map.items():
    if df.empty:
        continue

    col_i = col_idx_map[year_key]
    year_label = "2021 vs 2022" if year_key == '21_22' else "2022 vs 2023"
    
    for gubun, row_i in row_idx_map.items():
        ax = axes[row_i][col_i]
        eng_type = type_eng_map[gubun]
        
        plot_data = df[df['구분'] == gubun].copy()
        if plot_data.empty:
            continue
            
        plot_data['도시_권역'] = plot_data['city'] + '(' + plot_data['region'] + ')'
        plot_data['도시_권역'] = plot_data['도시_권역'].str.replace('기타\(기타\)', '기타', regex=True)
        plot_data = plot_data.sort_values(by='gap_vol', ascending=False).reset_index(drop=True)

        # 💡 [핵심] 현재 차트(연도, 구분)에 해당하는 강조 도시 리스트 추출
        current_highlights = highlight_map.get((year_key, gubun), [])

        # 2. 색상 설정 (현재 차트의 강조 리스트에 포함된 경우만 Accent Color)
        colors = []
        for idx, row in plot_data.iterrows():
            city_name = row['city']
            val = row['gap_vol']
            
            # 해당 차트의 강조 도시 목록에 있는 경우
            if city_name in current_highlights:
                colors.append('#2B5C8F' if val > 0 else '#C44E52')
            # 그 외 지자체 및 기타는 무채색/회색 톤다운
            else:
                colors.append("#E3A7A9B7")


        # 3. Barplot 그리기
        sns.barplot(
            data=plot_data, 
            x='gap_vol', 
            y='도시_권역', 
            hue='도시_권역',
            palette=colors,
            legend=False,
            ax=ax,
            zorder=1
        )

        # 4. 여백 조정 및 지수표기 제거
        x_min, x_max = ax.get_xlim()
        x_range = x_max - x_min
        ax.set_xlim(x_min - x_range * 0.12, x_max + x_range * 0.12)
        ax.xaxis.get_major_formatter().set_scientific(False)

        # 5. 수치 라벨 추가
        for idx, row in plot_data.iterrows():
            val = row['gap_vol']
            val_in_10k = val / 10000.0
            val_text = f"{val_in_10k:+.1f}만"
            
            offset = x_range * 0.02
            x_pos = val + offset if val >= 0 else val - offset
            align = 'left' if val >= 0 else 'right'
            
            ax.text(x_pos, idx, val_text, va='center', ha=align, fontsize=10, fontweight='bold', zorder=3)

        # 6. 축 라벨 깔끔하게 정리 (City (Region) 텍스트 위치 보정)
        ax.axvline(0, color='black', linestyle='--', linewidth=1, zorder=2)
        ax.set_title(f"[{year_label}] Cargo Volume Change ({eng_type.capitalize()})", fontsize=14, fontweight='bold', pad=12)
        
        # X축, Y축 메인 라벨 제거 (어차피 각 지자체 이름이 나오고 안내 박스가 있으므로 제거)
        ax.set_xlabel("", fontsize=0) 
        ax.set_ylabel("", fontsize=0)
        ax.grid(axis='x', linestyle=':', alpha=0.6, zorder=0)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x/10000)}만' if x != 0 else '0'))

        # 💡 [핵심] 좌측 상단에 축 정보 및 단위 통합 박스 배치
        ax.text(0.02, 0.92, "Y: 도시 (권역)  |  Unit: 만 톤 (10k Tons)", transform=ax.transAxes, 
                fontsize=9, color='#444444', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#CCCCCC', alpha=0.8),
                zorder=4)

# 메인 타이틀
fig.suptitle("Regional O/D Freight Flow Shift Analysis (2021-2023)", fontsize=18, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0.02, 1, 0.95])

save_path = save_dir / "cargo_flow_shift_dashboard_2x2.jpg"
plt.savefig(save_path, dpi=300, pil_kwargs={'quality': 95})
plt.close()