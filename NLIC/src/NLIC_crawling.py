import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.service import Service as EdgeService
import tkinter as tk
from tkinter import ttk
from webdriver_manager.microsoft import EdgeChromiumDriverManager

driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))

# NLIC page URL
url = "https://www.nlic.go.kr/nlic/frghtRoad0010.action"
driver.get(url)
time.sleep(3)  # await for the page to load

target_years = ["2020", "2021", "2022", "2023"]  # list of target years

# Loop through each target year and process the data
for year in target_years:
    print(f"Processing year: {year}")

    try:
        dropdown_element = driver.find_element(By.ID, "S_TOYEAR") # select the year dropdown element
        dropdown = Select(dropdown_element)
        dropdown.select_by_value(year)
        print(f"Year {year} selected in the dropdown.")
        time.sleep(1)

        search_button = driver.find_element(By.CSS_SELECTOR, "button.btn-md[type='submit']") #click the search button to submit the form
        search_button.click()
        print("button clicked. awaiting results...")
        time.sleep(5)
    except Exception as e:
        print(f"error while working: {e}")
        time.sleep(10)
        continue  # skip to the next year if an error occurs

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    boxes = soup.find_all('div', class_='box W_1785px')

    # extract the column(destination) data
    columns_ul = boxes[0].find_all('ul')
    DATA_PER_COLUMN = len(columns_ul) # number of column(destination) items
    all_columns = [li.get_text(strip=True) for li in columns_ul] # extract destination data
    DEAJEON_COLUMN_INDEX = next(i for i, li in enumerate(columns_ul) if "대전" in li.get_text())  # find the index of Daejeon in the column list

    # extract the row(departure) data
    rows_lis = soup.find_all('li', class_='con_list')
    DATA_PER_ROW = len(rows_lis) # number of row(departure) items
    all_rows = [li.get_text(strip=True) for li in rows_lis] # extract departure data
    DEAJEON_ROW_INDEX = next(i for i, li in enumerate(rows_lis) if "대전" in li.get_text())  # find the index of Daejeon in the row list

    # extract the data for Daejeon(departure) and match it with the destination data
    start_index = DEAJEON_ROW_INDEX * DATA_PER_COLUMN
    end_index = start_index + DATA_PER_COLUMN

    daejeon_lis = boxes[1].find_all('ul')[start_index:end_index] # extract the value of Daejeon(departure) from the data table
    daejeon_con = [li.get_text(strip=True) for li in daejeon_lis]

    matching_result = dict(zip(all_columns, daejeon_con)) # match the destination data with the Daejeon(departure) data

    # extract the data for Daejeon(destination) and match it with the departure data
    row_counter = 0   # the counter for the departure data
    arrival_result = {} # the result dictionary for the arrival data
    current_row = [] # the current row of data being processed

    for ul in boxes[1].find_all('ul'):  
        data_value = ul.find('li')
        if data_value:
            data_value = data_value.get_text(strip=True)
            current_row.append(data_value)
        else:
            current_row.append('0')

        style_attr = ul.get('style', '') # scan up to find the 'border-right' style attribute to identify the end of a row
        if 'border-right' in style_attr:
            if DEAJEON_COLUMN_INDEX < len(current_row):
                deajeon_dest=current_row[DEAJEON_COLUMN_INDEX] # extract the value of Daejeon(destination) from the current row
                if row_counter <len(rows_lis):
                    arrival_result[all_rows[row_counter]] = deajeon_dest # match the departure data with the Daejeon(destination) data
            current_row = []
            row_counter += 1
        

    df_departure = pd.Series(matching_result, name=f'{year} 년 대전 출발') # Deajun(departure) data series
    df_arrival = pd.Series(arrival_result, name=f'{year} 년 대전 도착') # Deajeon(destination) data series

    df_final = pd.concat([df_departure, df_arrival], axis=1) # combine the two series into a dataframe
    df_final.index.name = '지역' # set the index name to 'erea'

    csv_filename = f'Deajeon_logistics_{year}.csv'
    df_final.to_csv(csv_filename, encoding='utf-8-sig') # save the dataframe to a CSV file
    print(f"completed processing for year {year}. Data saved to {csv_filename}.")

    time.sleep(2)  # wait for 2 seconds before processing the next year

driver.quit()  # close the browser after processing all years
print("\nAll years processed. Browser closed.")