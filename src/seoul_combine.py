import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 1. 경로 설정 (저장용 output 폴더 생성)
base_dir = Path("./Seoul_household_logi")
target_dir = base_dir / "data" / "o-s"  # 불러올 데이터 폴더
save_dir = base_dir / "data"  # 결과 저장할 폴더
save_dir.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 자동 생성

# 한글 폰트 설정
plt.rc("font", family="Malgun Gothic")
plt.rc("axes", unicode_minus=False)

# 2. 모든 CSV 파일 경로 가져오기 및 합치기
all_files = glob.glob(os.path.join(target_dir, "*.csv"))

df_list = []
for file in all_files:
    filename = os.path.basename(file)
    ym = filename.split("_")[-1].replace(".csv", "")

    try:
        temp_df = pd.read_csv(file)
    except:
        temp_df = pd.read_csv(file, encoding="cp949")

    # 연월 및 연도/월 컬럼 추가
    temp_df["YYYYMM"] = ym
    temp_df["YEAR"] = ym[:4]
    temp_df["MONTH"] = ym[4:]

    df_list.append(temp_df)

# 통합 데이터프레임 생성
df = pd.concat(df_list, ignore_index=True)

print(f"✅ 총 {len(all_files)}개 파일 통합 완료! (총 행 수: {len(df):,}개)")

# 3. save_dir에 저장하기
output_file1 = save_dir / "merged_o_s_data.csv"
output_file2 = save_dir / "merged_s_s_data.csv"
output_file3 = save_dir / "merged_s_o_data.csv"

# index=False: 불필요한 인덱스 번호 저장 방지
# encoding="utf-8-sig": 엑셀에서 한글 깨짐 없이 바로 열리도록 설정
df.to_csv(output_file1, index=False, encoding="utf-8-sig")
df.to_csv(output_file2, index=False, encoding="utf-8-sig")
df.to_csv(output_file3, index=False, encoding="utf-8-sig")


print(f"💾 성공적으로 저장되었습니다: {output_file}")
