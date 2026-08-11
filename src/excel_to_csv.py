from pathlib import Path
import pandas as pd

data_dir = Path("./data")

# data 폴더 안의 모든 .xlsx 파일 검색 후 CSV 변환
for excel_file in data_dir.glob("*.xlsx"):
    df = pd.read_excel(excel_file)

    # 확장자만 .csv로 바꿔서 저장 경로 생성
    csv_path = excel_file.with_suffix(".csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"✅ 변환 완료: {csv_path.name}")
