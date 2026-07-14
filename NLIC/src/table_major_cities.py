import pandas as pd

# Load the actual data
df1 = pd.read_csv("major_cities_arrival.csv")

# Filter the top 12 rows based on the absolute value of the change
df1['abs_gap'] = df1['물동량_변화량'].abs()
df1_top = df1.sort_values(by='abs_gap', ascending=False).head(12).copy()

# Apply thousands separator (comma) formatting to numbers
df1_top['물동량_변화량'] = df1_top['물동량_변화량'].apply(lambda x: f"{x:+,}" if x > 0 else f"{x:,}")

# Save as an HTML table
columns_to_show = ['구분', '도시명', '물동량_변화량'] 
df1_top[columns_to_show].to_html("table_major_cities_arrival.html", index=False, justify='center')    

# Load the actual data
df2 = pd.read_csv("major_cities_departure.csv")

# Filter the top 12 rows based on the absolute value of the change
df2['abs_gap'] = df2['물동량_변화량'].abs()
df2_top = df2.sort_values(by='abs_gap', ascending=False).head(12).copy()

# Apply thousands separator (comma) formatting to numbers
df2_top['물동량_변화량'] = df2_top['물동량_변화량'].apply(lambda x: f"{x:+,}" if x > 0 else f"{x:,}")

# Save as an HTML table
df2_top[columns_to_show].to_html("table_major_cities_departure.html", index=False, justify='center')