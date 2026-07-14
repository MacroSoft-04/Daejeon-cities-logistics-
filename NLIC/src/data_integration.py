import pandas as pd

years = ['2020', '2021', '2022', '2023']
df_list = []

#append each year's DataFrame to the list
for year in years:
    filename = f"rawdata/Deajeon_logistics_{year}.csv"
    df = pd.read_csv(filename, index_col='지역')
    df_list.append(df)

# Concatenate all DataFrames in the list along the columns (axis=1)
df_total = pd.concat(df_list, axis=1)

df_total.to_csv("data_logistics_total.csv", encoding='utf-8-sig')