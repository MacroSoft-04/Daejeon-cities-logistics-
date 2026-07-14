import pandas as pd

df = pd.read_csv("data_logistics_total.csv")
df_melted = df.melt(id_vars=['지역'], var_name='year_type', value_name='물동량')

# process the 'cargo volume' (remove commas and convert to numeric type)
df_melted['물동량'] = df_melted['물동량'].astype(str).str.replace(',', '')
df_melted['물동량'] = pd.to_numeric(df_melted['물동량'], errors='coerce').fillna(0).astype(int)

df_melted['연도'] = df_melted['year_type'].str.extract(r'(\d{4})').astype(int) # extract the year from the 'year_type' column
df_melted['구분'] = df_melted['year_type'].apply(lambda x: '출발' if '출발' in x else '도착') # determine the type (departure or arrival) based on the 'year_type' column

df_melted['기준지역'] = '대전' # add a new column for the reference area
df_melted = df_melted.rename(columns={'지역': '대상지역'}) # rename the 'area' column to 'target area'

df_final = df_melted[['연도', '기준지역', '대상지역', '구분', '물동량']] # reorder the columns
df_final.to_csv("data_logistics_cleaned.csv", index=False, encoding='utf-8-sig') # save the final DataFrame to a CSV file