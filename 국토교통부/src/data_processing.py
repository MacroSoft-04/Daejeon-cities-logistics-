from pathlib import Path
import pandas as pd

# 1. 파일 경로 설정
current_dir = Path(__file__).resolve().parent
data_dir = current_dir.parent / "data"

raw_csv_path = data_dir / "domestic_wh_reg_raw.csv"
processed_csv_path = data_dir / "processed_wh_info.csv"

# 2. 수집해둔 CSV 파일 읽어오기
df = pd.read_csv(raw_csv_path)

# 3. 주소 전처리 (COMPANY_ADDRESS에서 첫 번째 단어 추출)
if "COMPANY_ADDRESS" in df.columns:
    # 결측치(빈값) 예외 처리 후 첫 단어(시/도) 추출
    df["SIDO"] = df["COMPANY_ADDRESS"].fillna("").astype(str).str.split().str[0]

if "WARE_NO" in df.columns:
    # 결측치 예외 처리 후, 등록번호 앞 4자리(연도)만 추출
    df["YEAR"] = df["WARE_NO"].fillna("").astype(str).str[:4]

# 1. 텍스트/문자열 컬럼의 결측치 처리 (비어 있으면 '정보없음' 또는 '-' 등으로 채우기)
text_columns = ['PRESIDENT_NAME', 'STORAGE_ITEM', 'COMPANY_NAME', 'COMPANY_TEL']
for col in text_columns:
    if col in df.columns:
        df[col] = df[col].fillna('정보없음')

# 2. 숫자/면적 컬럼의 결측치 처리 (비어 있으면 0으로 채우기)
numeric_columns = ['FROZEN_AREA', 'RNUM', 'FROZEN_WING_COUNT', 'GENERAL_WING_COUNT', 'GENERAL_AREA', 'STORAGE_AREA']
for col in numeric_columns:
    if col in df.columns:
        df[col] = df[col].fillna(0)


# 4. 전처리된 데이터 새로운 CSV로 저장
df.to_csv(processed_csv_path, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"saved file: {processed_csv_path.resolve()}")
print("=" * 60)