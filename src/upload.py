import sys
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine


def upload_csv_to_db(file_name: str, table_name: str = None):
    """
    CSV 파일을 읽어 MySQL DB 테이블로 일괄 적재하는 유틸리티 함수
    """
    load_dotenv()
    db_password = os.getenv("DB_PASSWORD")

    if not db_password:
        raise ValueError(".env 파일에서 DB_PASSWORD를 찾을 수 없습니다.")

    # 1. 경로 설정
    base_dir = Path(".")
    csv_path = base_dir / "data" / file_name

    if not csv_path.exists():
        print(f"❌ 에러: {csv_path} 파일이 존재하지 않습니다.")
        return

    # 2. 테이블명 미지정 시 파일명(확장자 제외)을 기본값으로 사용
    if not table_name:
        table_name = csv_path.stem

    # 3. 데이터 로드 및 DB 연결
    df = pd.read_csv(csv_path)
    password = quote_plus(db_password)
    engine = create_engine(
        f"mysql+pymysql://root:{password}@localhost:3306/mysql", echo=False
    )

    # 4. DB 적재
    df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)
    print(f"✅ 성공: '{csv_path}' -> DB 테이블 '{table_name}' ({len(df)}건 적재 완료)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        upload_csv_to_db(target_file)
    else:
        # 인자 없이 실행 시 기본 파일 업로드
        upload_csv_to_db("tradedata_dj_2020_2026.csv")
