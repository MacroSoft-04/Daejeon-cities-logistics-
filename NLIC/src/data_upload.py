from urllib.parse import quote_plus
from sqlalchemy import create_engine
import pandas as pd
from pathlib import Path

base_dir = Path(".")
data_dir = base_dir / "NLIC" / "data"

df= pd.read_csv(data_dir/"data_logistics_cleaned.csv")
password = quote_plus("Alstj0404!")
engine = create_engine(f'mysql+pymysql://root:{password}@localhost:3306/mysql', echo=False)
df.to_sql(name='data_logistics_cleaned', con=engine, if_exists='replace', index=False)