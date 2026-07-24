import pandas as pd
from pathlib import Path

# 1. Dictionary mapping region names to English
region_map = {
    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
}

# 2. Read existing data
data_dir = Path("./NLIC/data")
data_dir.mkdir(parents=True, exist_ok=True)
csv_file = Path(data_dir/"data_logistics_cleaned.csv")
df = pd.read_csv(csv_file)

# 3. Add English region column (mapped from '대상지역')
df['대상지역_en'] = df['대상지역'].map(region_map)

# 4. Reorder columns (place English region right next to '대상지역')
df = df[['연도', '기준지역', '대상지역', '대상지역_en', '구분', '물동량']]

# 5. Save to CSV
df.to_csv(data_dir/"data_logistics_cleaned.csv", index=False, encoding='utf-8-sig')