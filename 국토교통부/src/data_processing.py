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



# 4. 전처리된 데이터 새로운 CSV로 저장
df.to_csv(processed_csv_path, index=False, encoding="utf-8-sig")

print("\n" + "=" * 60)
print(f"saved file: {processed_csv_path.resolve()}")
print("=" * 60)