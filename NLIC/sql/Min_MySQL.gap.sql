WITH base_gap AS (
    SELECT 
        대상지역 AS 도시명,
        대상지역_en AS 도시명_en,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS 권역,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN 'Chungcheong'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS region_en,
        구분,
        SUM(CASE WHEN 연도 = 2021 THEN 물동량 ELSE 0 END) AS vol_2021,
        SUM(CASE WHEN 연도 = 2022 THEN 물동량 ELSE 0 END) AS vol_2022,
        -- Calculate the volume difference between 2022 and 2021
        SUM(CASE WHEN 연도 = 2022 THEN 물동량 ELSE 0 END) - SUM(CASE WHEN 연도 = 2021 THEN 물동량 ELSE 0 END) AS gap_vol
    FROM 
        data_logistics_cleaned
    WHERE 
        연도 IN (2021, 2022)
    GROUP BY 
        대상지역, 구분, 대상지역_en
),
ranked_gap AS (
    SELECT 
        *,
        -- Rank by absolute volume change in descending order
        ROW_NUMBER() OVER (PARTITION BY 구분 ORDER BY ABS(gap_vol) DESC) AS rank_num
    FROM base_gap
)
-- Keep city name for Top 5, group 6th place and lower into 'Others'
SELECT 
    구분,
    CASE  -- city name
        WHEN rank_num <= 4 THEN 도시명 
        ELSE '기타 (13개 지자체)' 
    END AS city,
    CASE  -- region
        WHEN rank_num <= 4 THEN 권역 
        ELSE '기타' 
    END AS region,
    CASE  -- region
        WHEN rank_num <= 4 THEN region_en 
        ELSE 'Others' 
    END AS region_en,
    CASE 
        WHEN rank_num <= 4 THEN 도시명_en 
        ELSE 'Others (13 Local Govs)' 
    END AS city_en,
    SUM(vol_2021) AS total_2021,
    SUM(vol_2022) AS total_2022,
    SUM(gap_vol) AS gap_vol
FROM 
    ranked_gap
GROUP BY 
    구분,
    CASE WHEN rank_num <= 4 THEN 도시명 ELSE '기타 (13개 지자체)' END,
    CASE WHEN rank_num <= 4 THEN 권역 ELSE '기타' END,
    CASE WHEN rank_num <= 4 THEN region_en ELSE 'Others' END,
    CASE WHEN rank_num <= 4 THEN 도시명_en ELSE 'Others (13 Local Govs)' END
ORDER BY 
    구분 ASC, 
    ABS(SUM(gap_vol)) DESC;



-- Cargo volume change amount between 2022 and 2023
WITH base_gap AS (
    SELECT 
        대상지역 AS 도시명,
        대상지역_en AS 도시명_en,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END AS 권역,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN 'Chungcheong'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END AS region_en,
        구분,
        SUM(CASE WHEN 연도 = 2022 THEN 물동량 ELSE 0 END) AS vol_2022,
        SUM(CASE WHEN 연도 = 2023 THEN 물동량 ELSE 0 END) AS vol_2023,
        -- Calculate the volume difference between 2022 and 2021
        SUM(CASE WHEN 연도 = 2023 THEN 물동량 ELSE 0 END) - SUM(CASE WHEN 연도 = 2022 THEN 물동량 ELSE 0 END) AS gap_vol
    FROM 
        data_logistics_cleaned
    WHERE 
        연도 IN (2022, 2023)
    GROUP BY 
        대상지역, 구분, 대상지역_en
),
ranked_gap AS (
    SELECT 
        *,
        -- Rank by absolute volume change in descending order
        ROW_NUMBER() OVER (PARTITION BY 구분 ORDER BY ABS(gap_vol) DESC) AS rank_num
    FROM base_gap
)
-- Keep city name for Top 5, group 6th place and lower into 'Others'
SELECT 
    구분,
    CASE  -- city name
        WHEN rank_num <= 4 THEN 도시명 
        ELSE '기타 (13개 지자체)' 
    END AS city,
    CASE  -- region
        WHEN rank_num <= 4 THEN 권역 
        ELSE '기타' 
    END AS region,
    CASE  -- region
        WHEN rank_num <= 4 THEN region_en 
        ELSE 'Others' 
    END AS region_en,
    CASE 
        WHEN rank_num <= 4 THEN 도시명_en 
        ELSE 'Others (13 Local Govs)' 
    END AS city_en,
    SUM(vol_2022) AS total_2022,
    SUM(vol_2023) AS total_2023,
    SUM(gap_vol) AS gap_vol
FROM 
    ranked_gap
GROUP BY 
    구분,
    CASE WHEN rank_num <= 4 THEN 도시명 ELSE '기타 (13개 지자체)' END,
    CASE WHEN rank_num <= 4 THEN 권역 ELSE '기타' END,
    CASE WHEN rank_num <= 4 THEN region_en ELSE 'Others' END,
    CASE WHEN rank_num <= 4 THEN 도시명_en ELSE 'Others (13 Local Govs)' END
ORDER BY 
    구분 ASC, 
    ABS(SUM(gap_vol)) DESC;