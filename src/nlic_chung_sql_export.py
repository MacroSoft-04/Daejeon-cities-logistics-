import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# 1. 환경변수 로드
load_dotenv()
db_password = os.getenv("DB_PASSWORD")
password = quote_plus(db_password)

# 2. DB 엔진 생성
engine = create_engine(
    f"mysql+pymysql://root:{password}@localhost:3306/mysql", echo=False
)

# 3. SQL 파일 경로 및 읽기
base_dir = Path(__file__).resolve().parent.parent
sql_file_path = (
    base_dir / "sql" / "nlic_chung_cargo_flow.sql"
)  # SQL 파일 경로에 맞게 수정

with open(sql_file_path, "r", encoding="utf-8") as f:
    sql_query = f.read()

# 4. DB에서 쿼리 직접 실행 및 DataFrame 변환
print("🔍 쿼리 실행 중...")
df = pd.read_sql(sql_query, con=engine)

# 5. CSV 저장
csv_path = base_dir / "data" / "nlic_chung_cargo_flow.csv"
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"💾 CSV 저장 완료 ({len(df)}행): {csv_path}")

# 6. MySQL DB 테이블로 다시 업로드
df.to_sql(name="nlic_chung_cargo_flow", con=engine, if_exists="replace", index=False)
print("✅ MySQL 테이블 업로드 완료!")
