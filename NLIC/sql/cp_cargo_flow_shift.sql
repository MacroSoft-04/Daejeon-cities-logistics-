-- Cargo volume change amount between 2021 and 2022 (Capital Area Merged)
WITH base_gap AS (
    SELECT 
        target_region,
        target_region AS target_region_en,
        
        -- Region classification
        CASE 
            WHEN target_region IN ('수도권') THEN '수도권'
            WHEN target_region IN ('대전', '세종', '충북', '충남') THEN '충청권'
            WHEN target_region IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'            
            WHEN target_region IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS region,
        
        CASE 
            WHEN target_region IN ('수도권') THEN 'Capital Area'
            WHEN target_region IN ('대전', '세종', '충북', '충남') THEN 'Chungcheong'
            WHEN target_region IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN target_region IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS region_en,
        
        flow_type,
        SUM(CASE WHEN year = 2021 THEN total_cargo_volume ELSE 0 END) AS vol_2021,
        SUM(CASE WHEN year = 2022 THEN total_cargo_volume ELSE 0 END) AS vol_2022,
        -- Calculate cargo volume change
        SUM(CASE WHEN year = 2022 THEN total_cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2021 THEN total_cargo_volume ELSE 0 END) AS gap_vol
    FROM 
        capital_city
    WHERE 
        year IN (2021, 2022)
    GROUP BY 
        target_region,
        flow_type
),
ranked_gap AS (
    SELECT 
        *,
        -- Rank by absolute change amount (Calculated with Capital Area combined)
        ROW_NUMBER() OVER (PARTITION BY flow_type ORDER BY ABS(gap_vol) DESC) AS rank_num
    FROM base_gap
)
-- Display top N cities only; 17 regions merged into 15, excluding top 4 leaves 11 remaining
SELECT 
    flow_type,
    CASE 
        WHEN rank_num <= 4 THEN target_region 
        ELSE '기타 (11개 지자체)' 
    END AS city,
    CASE 
        WHEN rank_num <= 4 THEN region 
        ELSE '기타' 
    END AS region,
    CASE 
        WHEN rank_num <= 4 THEN target_region_en 
        ELSE 'Others (11 Local Govs)' 
    END AS city_en,
    CASE 
        WHEN rank_num <= 4 THEN region_en 
        ELSE 'Others' 
    END AS region_en,
    SUM(vol_2021) AS total_2021,
    SUM(vol_2022) AS total_2022,
    SUM(gap_vol) AS gap_vol
FROM 
    ranked_gap
GROUP BY 
    flow_type,
    CASE WHEN rank_num <= 4 THEN target_region ELSE '기타 (11개 지자체)' END,
    CASE WHEN rank_num <= 4 THEN region ELSE '기타' END,
    CASE WHEN rank_num <= 4 THEN region_en ELSE 'Others' END,
    CASE WHEN rank_num <= 4 THEN target_region_en ELSE 'Others (11 Local Govs)' END
ORDER BY 
    flow_type ASC, 
    ABS(SUM(gap_vol)) DESC;



-- Cargo volume change amount between 2022 and 2023 (Capital Area Merged)
WITH base_gap AS (
    SELECT 
        target_region,
        target_region AS target_region_en,
        
        -- Region classification
        CASE 
            WHEN target_region IN ('수도권') THEN '수도권'
            WHEN target_region IN ('대전', '세종', '충북', '충남') THEN '충청권'
            WHEN target_region IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'            
            WHEN target_region IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS region,
        
        CASE 
            WHEN target_region IN ('수도권') THEN 'Capital Area'
            WHEN target_region IN ('대전', '세종', '충북', '충남') THEN 'Chungcheong'
            WHEN target_region IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN target_region IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS region_en,
        
        flow_type,
        SUM(CASE WHEN year = 2022 THEN total_cargo_volume ELSE 0 END) AS vol_2022,
        SUM(CASE WHEN year = 2023 THEN total_cargo_volume ELSE 0 END) AS vol_2023,
        -- Calculate cargo volume change
        SUM(CASE WHEN year = 2023 THEN total_cargo_volume ELSE 0 END) - SUM(CASE WHEN year = 2022 THEN total_cargo_volume ELSE 0 END) AS gap_vol
    FROM 
        capital_city
    WHERE 
        year IN (2022, 2023)
    GROUP BY 
        target_region,
        flow_type
),
ranked_gap AS (
    SELECT 
        *,
        -- Rank by absolute change amount (Calculated with Capital Area combined)
        ROW_NUMBER() OVER (PARTITION BY flow_type ORDER BY ABS(gap_vol) DESC) AS rank_num
    FROM base_gap
)
-- Display top N cities only; 17 regions merged into 15, excluding top 4 leaves 11 remaining
SELECT 
    flow_type,
    CASE 
        WHEN rank_num <= 4 THEN target_region 
        ELSE '기타 (11개 지자체)' 
    END AS city,
    CASE 
        WHEN rank_num <= 4 THEN region 
        ELSE '기타' 
    END AS region,
    CASE 
        WHEN rank_num <= 4 THEN target_region_en 
        ELSE 'Others (11 Local Govs)' 
    END AS city_en,
    CASE 
        WHEN rank_num <= 4 THEN region_en 
        ELSE 'Others' 
    END AS region_en,
    SUM(vol_2022) AS total_2022,
    SUM(vol_2023) AS total_2023,
    SUM(gap_vol) AS gap_vol
FROM 
    ranked_gap
GROUP BY 
    flow_type,
    CASE WHEN rank_num <= 4 THEN target_region ELSE '기타 (11개 지자체)' END,
    CASE WHEN rank_num <= 4 THEN region ELSE '기타' END,
    CASE WHEN rank_num <= 4 THEN region_en ELSE 'Others' END,
    CASE WHEN rank_num <= 4 THEN target_region_en ELSE 'Others (11 Local Govs)' END
ORDER BY 
    flow_type ASC, 
    ABS(SUM(gap_vol)) DESC;