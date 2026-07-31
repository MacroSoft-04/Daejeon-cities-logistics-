import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# 1. Load environment variables from .env file
load_dotenv()

# 2. Get database password from environment variables
db_password = os.getenv("DB_PASSWORD")

# Path setup
base_dir = Path("./Seoul_household_logi")
data_dir = base_dir / "data"
data_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(data_dir / "clean_seoul_logi_total.csv")

# 3. Encode password and create database engine
password = quote_plus(db_password)
engine = create_engine(
    f"mysql+pymysql://root:{password}@localhost:3306/mysql", echo=False
)

df.to_sql(name="clean_seoul_logi_total", con=engine, if_exists="replace", index=False)
