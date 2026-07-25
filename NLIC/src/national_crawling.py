import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import Select
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Initialize Edge Driver
driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))

# NLIC page URL
url = "https://www.nlic.go.kr/nlic/frghtRoad0010.action"
driver.get(url)
time.sleep(3)  # Await for page initialization

target_years = ["2019", "2020", "2021", "2022", "2023"]
all_years_dfs = []  # List to hold processed DataFrames for all target years

for year in target_years:
    print(f"\nProcessing year: {year}")

    try:
        # Select the target year from dropdown
        dropdown_element = driver.find_element(By.ID, "S_TOYEAR")
        dropdown = Select(dropdown_element)
        dropdown.select_by_value(year)
        print(f"Year {year} selected in dropdown.")
        time.sleep(1)

        # Submit search request
        search_button = driver.find_element(
            By.CSS_SELECTOR, "button.btn-md[type='submit']"
        )
        search_button.click()
        print("Searching... awaiting results...")
        time.sleep(5)
    except Exception as e:
        print(f"Error occurred while searching for year {year}: {e}")
        time.sleep(10)
        continue  # Skip to next year on exception

    soup = BeautifulSoup(driver.page_source, "html.parser")
    boxes = soup.find_all("div", class_="box W_1785px")

    if len(boxes) < 2:
        print(f"Warning: Data box not found for year {year}")
        continue

    # 1. Extract destinations (Column headers)
    columns_ul = boxes[0].find_all("ul")
    all_columns = [li.get_text(strip=True) for li in columns_ul]

    # 2. Extract origins (Row headers)
    rows_lis = soup.find_all("li", class_="con_list")
    all_rows = [li.get_text(strip=True) for li in rows_lis]

    # 3. Parse full matrix data
    matrix_data = []
    current_row = []

    for ul in boxes[1].find_all("ul"):
        data_value = ul.find("li")
        val = data_value.get_text(strip=True) if data_value else "0"

        # Remove commas and convert value to integer
        try:
            val_num = int(val.replace(",", ""))
        except ValueError:
            val_num = 0

        current_row.append(val_num)

        # Check 'border-right' style attribute to mark the end of a row
        style_attr = ul.get("style", "")
        if "border-right" in style_attr:
            matrix_data.append(current_row)
            current_row = []

    # 4. Create Matrix DataFrame (Rows: Departure/Origin, Columns: Destination)
    df_matrix = pd.DataFrame(
        matrix_data, index=all_rows[: len(matrix_data)], columns=all_columns
    )

    # 5. Transform matrix into long-format (Unpivot) for flexible analysis
    df_unstacked = df_matrix.stack().reset_index()
    df_unstacked.columns = ["기준지역", "대상지역", "물동량"]
    df_unstacked["연도"] = year
    df_unstacked["구분"] = "출발"  # Freight departure flow perspective

    all_years_dfs.append(df_unstacked)

    # Optional: Save yearly national matrix as individual CSV files
    df_matrix.to_csv(f"national_matrix_{year}.csv", encoding="utf-8-sig")
    print(f"Saved national matrix for year {year}.")

driver.quit()

# 6. Save combined multi-year dataset
if all_years_dfs:
    df_total = pd.concat(all_years_dfs, ignore_index=True)

    # Reorder columns: Year, Origin, Destination, Type, Volume
    df_total = df_total[["연도", "기준지역", "대상지역", "구분", "물동량"]]

    # Export merged dataset
    output_filename = "data_logistics_total_national.csv"
    df_total.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(
        f"\nNationwide data processing complete for all years! Saved to: {output_filename}"
    )