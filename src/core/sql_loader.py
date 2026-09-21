import sys
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine


def upload_csv_to_db(file_name: str, table_name: str = None):
    load_dotenv()
    db_password = os.getenv("DB_PASSWORD")

    if not db_password:
        raise ValueError("fail to load DB_PASSWORD from .env file")

    base_dir = Path(".")
    csv_path = base_dir / "data/processed" / file_name

    if not csv_path.exists():
        print(f"❌ file not found: {csv_path}")
        return

    if not table_name:
        table_name = csv_path.stem

    df = pd.read_csv(csv_path)
    password = quote_plus(db_password)
    engine = create_engine(
        f"mysql+pymysql://root:{password}@localhost:3306/mysql", echo=False
    )

    df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)
    print(f"success: '{csv_path}' -> DB table '{table_name}'")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        upload_csv_to_db(target_file)
    else:
        # if no argument is given, upload based on the file name
        upload_csv_to_db("tradedata_2000_2025_cleaned.csv")
