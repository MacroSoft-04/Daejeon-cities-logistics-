from urllib.parse import quote_plus
from sqlalchemy import create_engine
import pandas as pd
from pathlib import Path

base_dir = Path(".")
data_dir = base_dir / "NLIC" / "rawdata"

df= pd.read_csv(data_dir/"data_logistics_total_national.csv")
password = quote_plus("xxxx")
engine = create_engine(f'mysql+pymysql://root:{password}@localhost:3306/mysql', echo=False)
df.to_sql(name='data_logistics_total_national', con=engine, if_exists='replace', index=False)