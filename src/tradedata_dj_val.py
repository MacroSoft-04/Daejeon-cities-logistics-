from pathlib import Path
import pandas as pd

base_dir = Path(".")
data_dir = base_dir / "data"

nums = [20, 21, 22, 23, 24, 25, 26]

for num in nums:
    file_path = data_dir / f"tradedata_dj_{num}.csv"

    # 파일 감지 여부 출력
    if file_path.exists():
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except:
            df = pd.read_csv(file_path, encoding="cp949")

        # 읽어온 데이터의 기간(연도) 유니크 값 확인
        years = df["기간"].unique()
        print(f"✅ [{num}] 파일 찾음! 포함된 기간: {years[:3]}... (총 {len(df)}행)")
    else:
        print(f"❌ [{num}] 파일 없음! 경로 확인 필요: {file_path}")
