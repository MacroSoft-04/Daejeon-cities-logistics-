-- Cargo volume change amount between 2021 and 2022 (Capital Area Merged)
WITH base_gap AS (
    SELECT 
        -- 1. Combine Seoul, Gyeonggi, and Incheon into '수도권'
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            ELSE 대상지역
        END AS 도시명,
        
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            ELSE 대상지역_en
        END AS 도시명_en,
        
        -- Region classification
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
        -- Calculate cargo volume change
        SUM(CASE WHEN 연도 = 2022 THEN 물동량 ELSE 0 END) - SUM(CASE WHEN 연도 = 2021 THEN 물동량 ELSE 0 END) AS gap_vol
    FROM 
        data_logistics_cleaned
    WHERE 
        연도 IN (2021, 2022)
    GROUP BY 
        -- Ensure GROUP BY expressions strictly match SELECT expressions
        CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권' ELSE 대상지역 END,
        CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area' ELSE 대상지역_en END,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN 'Chungcheong'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END,
        구분
),
ranked_gap AS (
    SELECT 
        *,
        -- Rank by absolute change amount (Calculated with Capital Area combined)
        ROW_NUMBER() OVER (PARTITION BY 구분 ORDER BY ABS(gap_vol) DESC) AS rank_num
    FROM base_gap
)
-- Display top N cities only; 17 regions merged into 15, excluding top 4 leaves 11 remaining
SELECT 
    구분,
    CASE 
        WHEN rank_num <= 4 THEN 도시명 
        ELSE '기타 (11개 지자체)' 
    END AS city,
    CASE 
        WHEN rank_num <= 4 THEN 권역 
        ELSE '기타' 
    END AS region,
    CASE 
        WHEN rank_num <= 4 THEN region_en 
        ELSE 'Others' 
    END AS region_en,
    CASE 
        WHEN rank_num <= 4 THEN 도시명_en 
        ELSE 'Others (11 Local Govs)' 
    END AS city_en,
    SUM(vol_2021) AS total_2021,
    SUM(vol_2022) AS total_2022,
    SUM(gap_vol) AS gap_vol
FROM 
    ranked_gap
GROUP BY 
    구분,
    CASE WHEN rank_num <= 4 THEN 도시명 ELSE '기타 (11개 지자체)' END,
    CASE WHEN rank_num <= 4 THEN 권역 ELSE '기타' END,
    CASE WHEN rank_num <= 4 THEN region_en ELSE 'Others' END,
    CASE WHEN rank_num <= 4 THEN 도시명_en ELSE 'Others (11 Local Govs)' END
ORDER BY 
    구분 ASC, 
    ABS(SUM(gap_vol)) DESC;



-- Cargo volume change amount between 2022 and 2023 (Capital Area Merged)
WITH base_gap AS (
    SELECT 
        -- 1. Combine Seoul, Gyeonggi, and Incheon into '수도권'
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            ELSE 대상지역
        END AS 도시명,
        
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            ELSE 대상지역_en
        END AS 도시명_en,
        
        -- Region classification
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
        -- Calculate cargo volume change in 2023 compared to 2022
        SUM(CASE WHEN 연도 = 2023 THEN 물동량 ELSE 0 END) - SUM(CASE WHEN 연도 = 2022 THEN 물동량 ELSE 0 END) AS gap_vol
    FROM 
        data_logistics_cleaned
    WHERE 
        연도 IN (2022, 2023)
    GROUP BY 
        -- Ensure GROUP BY expressions strictly match SELECT expressions
        CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권' ELSE 대상지역 END,
        CASE WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area' ELSE 대상지역_en END,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN '수도권'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN '충청권'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN '영남권'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN '호남권'
            ELSE '기타'
        END,
        CASE 
            WHEN 대상지역 IN ('서울', '경기', '인천') THEN 'Capital Area'
            WHEN 대상지역 IN ('대전', '세종', '충북', '충남') THEN 'Chungcheong'
            WHEN 대상지역 IN ('부산', '대구', '울산', '경북', '경남') THEN 'Yeongnam'
            WHEN 대상지역 IN ('광주', '전북', '전남') THEN 'Honam'
            ELSE 'Others'
        END,
        구분
),
ranked_gap AS (
    SELECT 
        *,
        -- Rank by absolute change amount with Capital Area combined
        ROW_NUMBER() OVER (PARTITION BY 구분 ORDER BY ABS(gap_vol) DESC) AS rank_num
    FROM base_gap
)
-- Display top 4 local governments and group the remaining 11 local governments
SELECT 
    구분,
    CASE 
        WHEN rank_num <= 4 THEN 도시명 
        ELSE '기타 (11개 지자체)' 
    END AS city,
    CASE 
        WHEN rank_num <= 4 THEN 권역 
        ELSE '기타' 
    END AS region,
    CASE 
        WHEN rank_num <= 4 THEN region_en 
        ELSE 'Others' 
    END AS region_en,
    CASE 
        WHEN rank_num <= 4 THEN 도시명_en 
        ELSE 'Others (11 Local Govs)' 
    END AS city_en,
    SUM(vol_2022) AS total_2022,
    SUM(vol_2023) AS total_2023,
    SUM(gap_vol) AS gap_vol
FROM 
    ranked_gap
GROUP BY 
    구분,
    CASE WHEN rank_num <= 4 THEN 도시명 ELSE '기타 (11개 지자체)' END,
    CASE WHEN rank_num <= 4 THEN 권역 ELSE '기타' END,
    CASE WHEN rank_num <= 4 THEN region_en ELSE 'Others' END,
    CASE WHEN rank_num <= 4 THEN 도시명_en ELSE 'Others (11 Local Govs)' END
ORDER BY 
    구분 ASC, 
    ABS(SUM(gap_vol)) DESC;