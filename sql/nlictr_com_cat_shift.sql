-- Cargo volume change amount between 2021 and 2022 (Capital Area Merged)
SELECT 
    *,
    SUM(CASE WHEN year = 2019 THEN cargo_volume ELSE 0 END) AS vol_2019,
    SUM(CASE WHEN year = 2020 THEN cargo_volume ELSE 0 END) AS vol_2020,
    SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) AS vol_2021,
    SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) AS vol_2022,
    SUM(CASE WHEN year = 2023 THEN cargo_volume ELSE 0 END) AS vol_2023,
    -- Calculate cargo volume change
    SUM(CASE WHEN year = 2020 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2019 THEN cargo_volume ELSE 0 END) AS gap_19_20_vol,
    SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2020 THEN cargo_volume ELSE 0 END) AS gap_20_21_vol,
    SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2021 THEN cargo_volume ELSE 0 END) AS gap_21_22_vol,
    SUM(CASE WHEN year = 2023 THEN cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2022 THEN cargo_volume ELSE 0 END) AS gap_22_23_vol
FROM 
    nlictr_com_cat
WHERE  
    year IN (2019, 2020, 2021, 2022, 2023)
GROUP BY 
    year, region_kr, flow_type, commodity_category;
