import pandas as pd
from sqlalchemy import create_engine

df= pd.read_csv('data_logistics_cleaned.csv')

engine = create_engine('mysql+pymysql://root:xxxx@localhost:3306/mysql', echo=False)
df.to_sql(name='data_logistics_cleaned', con=engine, if_exists='replace', index=False)